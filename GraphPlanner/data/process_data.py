import json
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import glob
from tqdm import tqdm
from GraphLink.tool import ApiInfo
from utils.utilize import observation_shorten,write_file,observation_shortenstr20

def transform_get_room_availability(original_response):
    if original_response  in ({},[],"") or  "error" in original_response\
            or "bgo_error"  in original_response:
        return original_response
    # 提取原始数据
    lengths_of_stay = original_response.get("lengthsOfStay", [])
    currency = original_response.get("currency", "")
    av_dates = original_response.get("avDates", [])

    # 转换 lengthsOfStay
    transformed_lengths_of_stay = [
        {"date": list(item.keys())[0], "min_nights": list(item.values())[0]}
        for item in lengths_of_stay
    ]

    # 转换 avDates
    transformed_av_dates = [
        {"date": list(item.keys())[0], "price": list(item.values())[0]}
        for item in av_dates
    ]

    # 返回目标格式
    return {
        "currency": currency,
        "avDates": transformed_av_dates,
        "lengthsOfStay": transformed_lengths_of_stay
    }

def get_static_response():
    file  = "/home/snrobot/lin/GraphLinkTools/Tools/Static_Response(1).json"
    with open(file, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
        # 用于存储每个 function_name 最长 observation
    max_observations = {}

    for entry in json_data:
        func_name = entry.get("function_name")
        if func_name == "Get_Room_List_With_Availability":
            observation = {}
            observation["available"] = entry.get("observation")["available"]
            observation["unavailable"] = entry.get("observation").get("unavailable",{})
        else:
            observation = entry.get("observation")["data"]
        # 计算 observation 的字符串长度（可替换为其他指标）
        obs_str = json.dumps(observation)
        obs_length = len(obs_str)

        # 如果当前 function_name 尚未记录，或者当前 observation 更长，则更新
        if (
            func_name not in max_observations
            or obs_length > len(json.dumps(max_observations[func_name]))
        ):
            if func_name == "Get_Room_Availability" : max_observations[func_name] = transform_get_room_availability(observation)
            else:
                max_observations[func_name] = observation

    return max_observations

def new_apidata(max_observations):
    api_folder_path = "/home/snrobot/lin/GraphLinkTools/GraphPlanner/data/ApiInfo_update(1)"
    output_folder = "/home/snrobot/lin/GraphLinkTools/GraphPlanner/data/APIinfo_update(3)"
    info_files = glob.glob(os.path.join(api_folder_path, '*.json'))
    notebooks = {}
    for i, file_path in enumerate(info_files):
        notebook = ApiInfo(**json.load(open(file_path)))
        notebooks[notebook.name] = notebook
    
    for i, notebook in tqdm(enumerate(notebooks.values()), total=len(notebooks), desc="Processing APIs"):
        name = notebook.name
        if name not in max_observations:
            continue
        print(name)
        filtered_data = {
            "name":name,
            "docs_row":notebook.docs_row,
            "api_response_schema":observation_shortenstr20(max_observations[name], 1),
        }
        write_file(filtered_data, f"{output_folder}/{name}.json")

# 从gt中抽取文档描述
def get_docs_from_gt():
    file = "/home/snrobot/lin/GraphLinkTools/GraphPlanner/ComplexFuncBench/data/ComplexFuncBench.jsonl"
    with open(file, 'r') as f:
        datas = [json.loads(line) for line in f]
    
    
    dir = "/home/snrobot/lin/GraphLinkTools/GraphPlanner/data/APIinfo_update(3)"
    files =  glob.glob(os.path.join(dir, '*.json'))
    notebooks = {}
    for f in files:
        with open(f, 'r') as f:
            notebook = json.load(f)
            notebooks[notebook["name"]] = notebook
    
    notebooks1 = {}
    for data in datas:
        fcs = data["functions"]
        for f in fcs:
            notebooks1[f["name"]] = f
    for k, v in notebooks1.items():
        if k not in notebooks:
            notebooks1[k] = {"name": k, "docs_row": v}
        else:
            notebooks1[k] = {"name" : k, "docs_row": v, "api_response_schema": notebooks[k]["api_response_schema"]}
    out_dir = "/home/snrobot/lin/GraphLinkTools/GraphPlanner/data/ApIinfo_update(4)"
    for k, v in notebooks1.items():
        f = open(os.path.join(out_dir, k + ".json"), "w")
        f.write(json.dumps(v, indent=4, ensure_ascii=False))
        
def count_lose_data():
    a = set()
    file = "/home/snrobot/lin/GraphLinkTools/Tools/Static_Response(1).json"
    with open(file, 'r') as f:
        notebooks = json.load(f)
    for note in notebooks:
        obs = note['observation']
        if 'data' not in obs:
            a.add(note['function_name'])
    print(a)



        
    


if __name__ == "__main__":
#    dir = "/home/snrobot/lin/GraphLinkTools/GraphPlanner/data/APIinfo_update(3)"
#    files =  glob.glob(os.path.join(dir, '*.json'))
#    print(len(files))
#     # get_docs_from_gt()
    count_lose_data()