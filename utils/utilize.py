import sys
import pickle
import multiprocessing
import json
import os
from tqdm import tqdm
import re
import glob
from transformers import AutoTokenizer
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from GraphLink.tool import ApiInfo
from jsonpath_ng import jsonpath, parse
import copy
import readline


def write_file(data,filename,num_processes=20,default_name='train',indent=4):
    if filename.endswith('.json'):
        json.dump(data,open(filename,'w'),indent=indent)
    elif filename.endswith('.jsonl') :
        with open(filename, 'w') as f:
            for line in data:
                f.write(json.dumps(line) + '\n')
    elif filename.endswith('.txt'):
        with open(filename, 'w') as f:
            for line in data:
                f.write(str(line) + '\n')
    elif filename.endswith('.pkl'):
        pickle.dump(data,open(filename,'w'))
    elif '.' not in filename:
        multi_write_jsonl(data,filename,num_processes=num_processes,default_name=default_name)
    else:
        raise "no suitable function to write data"

def write_jsonl(data,filename,ids=None):
    with open(filename,'w') as f:
        for line in tqdm(data):
            f.write(json.dumps(line)+'\n')
    return ids,len(data)

def multi_write_jsonl(data,folder,num_processes=10,default_name='train'):
    """

    :param filename:
    :param num_processes:
    :return:
    """
    if not os.path.exists(folder):
        os.makedirs(folder)
    length = len(data) // num_processes + 1
    pool=multiprocessing.Pool(processes=num_processes)
    collects=[]
    for ids in range(num_processes):
        filename=os.path.join(folder,f"{default_name}{ids}.jsonl")
        collect = data[ids * length:(ids + 1) * length]
        collects.append(pool.apply_async(write_jsonl,(collect,filename,ids)))

    pool.close()
    pool.join()
    cnt=0
    for i,result in enumerate(collects):
        ids,num=result.get()
        assert ids==i
        cnt+=num
    return cnt

def strip_json_markdown(text):
    if text.startswith("```"):
        text = text.strip("`").strip()
        if text.startswith("json"):
            text = text[len("json"):].strip()
    return text

def observation_shorten(response, i):
    if response == None:
        return response

    if isinstance(response, dict):
        # keys_to_delete = [key for key, value in response.items() if (value in ["", None, {}, []])]
        # for key in keys_to_delete:
        #     response.pop(key)

        for key, value in response.items():
            response[key] = observation_shorten(value, i)
            
    elif isinstance(response, list):
        if len(response) > i:
            response = response[-i:]
        response = [observation_shorten(item, i) for item in response]

    return response
def observation_shortenstr20(response, i):
    if response is None:
        return response

    if isinstance(response, dict):
        for key, value in response.items():
            if isinstance(value, str) and len(value) > 100:
                # 如果值是字符串且长度大于20，截取前20个字符
                response[key] = value[:100]
            else:
                # 递归调用
                response[key] = observation_shortenstr20(value, i)

    elif isinstance(response, list):
        # 首先截取列表，只保留最后 i 个元素
        response = response[-i:]

        # 对列表中的每个字符串元素进行处理
        response = [item[:100] if isinstance(item, str) and len(item) > 100 else observation_shortenstr20(item, i) for item in response]

    return response

def count_tokens(text):
    tokenizer = AutoTokenizer.from_pretrained("/home/snrobot/lin/Llm-model/qwen2.5-7b")
    # 根据 text 的类型进行处理
    if isinstance(text, (dict, list)):
        # 如果是字典或列表，转换为 JSON 字符串
        text_str = json.dumps(text, ensure_ascii=False, indent=4)
    elif isinstance(text, str):
        # 如果是字符串，直接使用
        text_str = text
    else:
        # 其他类型（如数字、布尔值等），转换为字符串
        text_str = str(text)
    
    # 使用 tokenizer 编码并计算 Token 数量
    tokens = tokenizer.encode(text_str)
    token_count = len(tokens)
    return token_count

# 对响应字段进行路径搜索
def extract_fields(schema, path=''):
    fields = []
    if 'description' in schema and isinstance(schema['description'], str):
        name = path.split(".")[-1]
        fields.append({"path_name":path.strip('.'), 
                        "name":name,
                        "description":schema['description']})
    
    if isinstance(schema, dict): 
        for key, value in schema.items():
            if key in ['type', 'description'] and isinstance(value, str):
                continue
            if key not in ('ob_properties', 'ar_items'):
                new_path = f"{path}.{key}" if path else key
            elif key == 'ob_properties':
                new_path = path
            elif key == 'ar_items':
                new_path = f"{path}[]"
                
            fields.extend(extract_fields(value, new_path))
    
    if isinstance(schema, list):
        for item in schema:
            fields.extend(extract_fields(item, f"{path}[]"))    
        

    return fields

#对所有api进行处理
def process_apiInfo(api_folder, output_folder):
    info_files = glob.glob(os.path.join(api_folder, '*.json'))
    
    notebooks = {}
    for i, file_path in enumerate(info_files):
        notebook = ApiInfo(**json.load(open(file_path)))
        notebooks[notebook.name] = notebook
        
        os.makedirs(output_folder, exist_ok=True)
        file_path = os.path.join(output_folder, f'{notebook.name}.json')
        
        response = notebook.responses
        if response:
            result = response[0]["observation"]
            if "bgo_error" in result:
                notebook.update(verified=False, responses=None, enhance_resfield_desc=None)
                print("修改了verified为false")
        
        if not notebook.verified:
            print("skip", notebook.name)
            write_file(notebook.to_dict(), file_path)
            continue
        #params_desc_list 和 response_desc_list 字段
        # response_desc = []
        # for k,v in notebook.enhance_resfield_desc["response_fields"].items():
        #     response_desc.extend(extract_fields(v, k))
        if isinstance(notebook.enhance_resfield_desc["response_fields"], dict):
            response_desc = extract_fields(notebook.enhance_resfield_desc["response_fields"], "$")
        else:
            response_desc = extract_fields(notebook.enhance_resfield_desc["response_fields"], "$")
            
        notebook.update(response_desc_list=response_desc)
        
        write_file(notebook.to_dict(), file_path)
        print(f"Saved to {file_path}")
        

#对原始文档进行增强，获取得到增强的文档
def get_row_api_info(notebook):
    docs_row = notebook.docs_row
    enhance_params_desc = notebook.enhance_params_desc
    
    merged_params = {}

    for param_name, param_info in docs_row["parameters"]["properties"].items():
        # 只有当原始 description 为空或不存在时，才使用增强的描述
        description = param_info.get("description", "").strip()
        
        if not description and param_name in enhance_params_desc["enhanced_parameters"]:
            merged_params[param_name] = {
                **param_info,
                "description": enhance_params_desc["enhanced_parameters"][param_name]
            }
        else:
            merged_params[param_name] = param_info
    
    docs_row_copy = copy.deepcopy(docs_row)
    docs_row_copy["parameters"] = {
            "type": "object",
            "properties": merged_params,
            "required": docs_row["parameters"].get("required", [])
        }
    if not notebook.enhance_func_desc:
        docs_row_copy["func_description"] = notebook.enhance_func_desc

    return docs_row_copy

#根据jsonpath获取响应中具体的值
def get_example_jsonpath(notebook, field, i):
    response = notebook.responses[0]["observation"]
    response = observation_shorten(response, i)
    res = None
    try:
        field =  re.sub(r"\[.*?\]", '[0]', field)
        expr = field
        jsonpath_expr = parse(expr)
    
        matches = jsonpath_expr.find(response)
        res = [{field:match.value} for match in matches]

    except Exception as e:
        print(f"Error processing field {field}")

    return res 

if __name__ == '__main__':
#     print("hhhh")
#     schema = {
#     "response_fields": {
#         "search_results": {
#             "type": "Array",
#             "description": "List of car rental options available for the search query.",
#             "ar_items": {
#                 "type": "Object",
#                 "description": "Details of a rental car option.",
#                 "ob_properties": {
#                     "car_model": {
#                         "type": "String",
#                         "description": "Car model name."
#                     }
#                 }
#             }
#         }
#     }
# }

#     fields = extract_fields(schema['response_fields'], "")
#     print(fields)
    
    api_info = "/home/snrobot/lin/GraphLinkTools/Tools(1)/ApiInfo(1)"
    output_folder = "/home/snrobot/lin/GraphLinkTools/Tools(1)/ApiInfo_update(1)"
    process_apiInfo(api_info, output_folder) 
        