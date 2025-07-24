from termcolor import colored

def print_colored(text, color=None):
    """
    打印彩色字符串。

    参数：
    - text: 要打印的文本
    - color: 文本颜色（如 red, green, blue, yellow, cyan, magenta, white）
    - on_color: 背景颜色（如 on_red, on_green, on_blue）
    - attrs: 属性列表（如 ['bold', 'dark', 'underline', 'blink', 'reverse', 'concealed']）
    """
    try:
        print('\n\n\n')
        print(colored(text, color=color))
        print('\n\n\n')
    except Exception as e:
        print(f"错误：{e}")

#去掉llm返回的参数填充结果中的null值
def contains_none_or_unknown(value):
    # 把整个值转成字符串，判断是否包含 'none' 或 'unknown'
    if value is None:
        return True
    return "none" in str(value).lower() or "unknown" in str(value).lower()

def remove_null_values(arguments, tool_args_info):
    flag = False
    keys_to_delete = []

    for arg, value in arguments.items():
        is_required = tool_args_info.get(arg, {}).get('required', False)

        if value is None or value == "null":
            if is_required:
                arguments[arg] = "unknown"
                flag = True
            else:
                keys_to_delete.append(arg)
        else:
            # 只用字符串判断，不替换，也不递归
            if contains_none_or_unknown(value):
                flag = True

    for key in keys_to_delete:
        del arguments[key]

    return flag, arguments


# 对 api调用进行格式化
def format_api_call(api_call):
    api_name = api_call.get("api_name")
    arguments = api_call.get("arguments", {})

    # 过滤掉 null 参数
    filtered_args = {k: v for k, v in arguments.items() if v is not None}

    # 把参数转换成 key = value 格式
    args_str = ", ".join(f'{key} = "{value}"' for key, value in filtered_args.items())

    # 拼接成函数调用形式
    return f"{api_name}({args_str})"

# 提取未知字段
def extract_unknown_fields(data, path="", results=None):
    pattern = re.compile(r'\w+\(.*?\)')
    if results is None:
        results = []

    if isinstance(data, dict):
        for key, value in data.items():
            new_path = f"{path}.{key}" if path else key
            extract_unknown_fields(value, new_path, results)

    elif isinstance(data, list):
        for index, item in enumerate(data):
            new_path = f"{path}[{index}]"
            extract_unknown_fields(item, new_path, results)

    elif (isinstance(data, str)):
        matches = pattern.findall(data)
        # for m in matches:
        #     print(m)
        if matches and matches[0].lower().startswith("unknown("):
            results.append(path)
    elif data is None:
        results.append(path)

    return results

import re

def normalize_param_name(param):
    """
    将 legs[0].fromId 格式转为 legs[].fromId
    """
    return re.sub(r'\[\d+\]', '[]', param)

# 从依赖图中找关系
def build_dependencies(all_links, used_tools, unknown_params):
    """
    构建依赖关系图，支持参数名称中带索引的情况，并且保持原始依赖项格式
    :param all_links: 所有参数依赖定义 dict
    :param unknown_params: 当前需要解析的参数名列表
    :param used_tools: 已使用工具的集合
    :return: 过滤后的依赖关系 dict
    """
    dependencies = {}
    source_api_list = []

    for param in unknown_params:
        normalized_param = normalize_param_name(param)

        if normalized_param not in all_links:
            continue

        valid_deps = []
        for dep_info in all_links[normalized_param]:
            # 只保留有效的依赖
            if dep_info.get("is_valid") not in (True, "candidate", "true"):
                continue

            source_api = dep_info.get("source_api")
            if "description:" in source_api:
                source_api = source_api.split("description:")[0].strip()
            # source_api 必须在 used_tools 中
            if source_api not in used_tools:
                continue

            source_api_list.append(source_api)  # 保留 source_api 名称

            # 保留原格式
            valid_deps.append({
                "source_api": source_api,
                "res_path": dep_info["source_api_respath"],
            })

        if valid_deps:
            dependencies[normalized_param] = valid_deps  # 这里仍然使用原 param，而不是 normalized_param，保留原始 key

    return dependencies, source_api_list

# 从 api参数调用中匹配 出 api调用
import re
def extract_api_calls_with_path(arguments):
    pattern = re.compile(r'\w+\(.*?\)')
    results = {}
    flag = False
    def recurse(value, path):
        nonlocal flag
        if isinstance(value, dict):
            for k, v in value.items():
                recurse(v, f"{path}.{k}" if path else k)
        elif isinstance(value, list):
            for i, item in enumerate(value):
                recurse(item, f"{path}[{i}]")
        elif isinstance(value, str):
            matches = pattern.findall(value)
            # for m in matches:
            #     # 如果一个字段多个调用，只取第一个？也可以存列表
            if matches and not matches[0].lower().startswith("unknown("):
                results[path] = matches[0]
            else:
                flag = True

    recurse(arguments, "")
    return results, flag # 输出extracted_calls

#构建边信息
def match_api_dependencies(extracted_calls, dependency, target_api, node_key):
    """
    extracted_calls = {"参数": "api调用xx(参数1, 参数2, 参数3)", ....}
dependency.get(target_api, {}) = {"参数1": [{关系}, {关系2}], "参数2": [{......}], ...}
    """
    results = []
    source_apis_in_args =[call.split("(")[0] for call in extracted_calls.values()]

    # 取目标 API 的依赖信息
    target_api_deps = dependency.get(target_api, {})

    # 遍历每个 target 参数 todo 改成遍历 target
    for params, source_call in extracted_calls.items():
        # 如果参数名中有索引，转换为通用格式
        normalized_param = normalize_param_name(params)
        call = source_call.split("(")[0]

        dep_list = target_api_deps.get(normalized_param, [])
        for dep in dep_list:
            source_api = dep.get("source_api").split("description:")[0].strip()
            if source_api == call:
                results.append({
                    "from_api": call,
                    "response_path": normalize_param_name(dep.get("source_api_respath")), # 统一格式化
                    "target_param": params,
                    "to_api": target_api,
                })

    return results




if __name__ == "__main__":
#     all_links = {
#     "legs[].fromId": [
#         {"target_api_params": "legs[].fromId", "source_api": "Search_Flight_Location", "source_api_respath": "$[0].id", "reason": "xxx", "is_valid": True},
#         {"target_api_params": "legs[].fromId", "source_api": "Another_API", "source_api_respath": "$[0].id", "reason": "xxx", "is_valid": True},
#     ]
# }
#     unknown_params = ["legs[0].fromId"]
#     used_tools = {"Search_Flight_Location"}
#     api_chain = build_dependencies(all_links, unknown_params, used_tools)
#     print(api_chain)
    arguments = {'latitude': 'Location_to_Lat_Long(query = "Four Seasons Resort Orlando at Walt Disney World Resort")', 'longitude': 'Location_to_Lat_Long(query = "Four Seasons Resort Orlando at Walt Disney World Resort")', 'languagecode': 'null'}
    tool_args_info = {
        "query": {"required": True}
    }

    flag, cleaned_arguments = remove_null_values(arguments.copy(), tool_args_info)
    print(flag)
    print(cleaned_arguments)
    exit()
# 模拟 API 参数说明
    extracted = {
    "legs[0].fromId": "Search_Flight_Location(query = \"Berlin\")",
    "legs[0].toId": "Search_Flight_Location(query = \"London\")",
    "legs[1].toId": "Search_Flight_Location(query = \"Berlin\")"
    }

    dependencies = {
        "Search_Car_Location": {
            "legs[].fromId": [
                {
                    "target_api_params": "query",
                    "source_api": "Search_Flight_Location",
                    "source_api_respath": "$[0].name",
                    "reason": "...",
                    "is_valid": True
                },
                {
                    "target_api_params": "query",
                    "source_api": "Search_Flights_Multi_Stops",
                    "source_api_respath": "$.flightOffers[0].segments[0].arrivalAirport.name",
                    "reason": "...",
                    "is_valid": True
                }
            ]
        }
    }
    res = match_api_dependencies(extracted, dependencies, "Search_Car_Location")
    print(res)

    # judege = {'api_name': 'Get_Flight_Details', 'arguments': {'token': 'Search_Flights(sort = "FASTEST", adults = "1", toId = "unknown(Los Angeles airport ID needs to be retrieved from another API)", fromId = "unknown(Guangzhou airport ID needs to be retrieved from another API)", departDate = "2024-12-10")(need to retrieve token from search flights API)'}}
    # res = extract_unknown_fields(judege['arguments'])
    # print(res)

