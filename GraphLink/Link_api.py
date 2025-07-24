from basellms import DeepSeekRequest, QwenRequest
from build_database import APIDocEmbedder
from queue import Queue
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from template.ApiLink_Prompts import ApiLinkPrompts, Fine_Grained2_Example
from utils.utilize import *
from tool import ApiInfo
from typing import Union, Dict,List
from logger import Logger
from rapidapi import RapidAPICall
import logging

from jsonpath_ng import jsonpath, parse
import json
import dotenv
import json
import random
import copy
import glob
dotenv.load_dotenv("/home/snrobot/lin/GraphLinkTools/.env")

import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

class LinkApi:
    def __init__(self, required_folder, api_info_path):
        self.required_folder = required_folder
        self.api_folder = api_info_path
        #链接向量数据库
        self.apiembedder = APIDocEmbedder(
            collection_name="api_docs_add_jsonpath",
            embed_model_name="/home/snrobot/lin/GraphLinkTools/sentence_similiary/all-MiniLM-L6-v2",
            gpt_base_url=None,
            dimension=384,
        )
        #定义两个队列分别处理出边和入边
        self.inq : Queue[ApiInfo] = Queue()
        self.outq:  Queue[ApiInfo] = Queue()
        
        #初始化gpt模块
        params = {
            "model_name": "deepseek-chat",
            "api_key": os.getenv("Deepseek_API_KEY"),
            "base_url": "https://api.deepseek.com"
        }
        self.llm = DeepSeekRequest(**params)
        self.response_format = {'type': 'json_object'}
        
        #加载调用api
        apis_info_path = "/home/snrobot/lin/GraphLinkTools/Tools(1)/all_apis.json"
        with open(apis_info_path, 'r') as f:
            tool = json.load(f)
        tool_info = tool['functions']
        self.rapidapi = RapidAPICall(tool="booking-com15", tool_info=tool_info)
        #加载提示词模板
        self.template = ApiLinkPrompts()
    
    #先寻找api的必须参数和响应
    def process_api_required_params(self):
        #把所有api信息汇聚一起
        info_files = glob.glob(os.path.join(self.api_folder, '*.json'))
        notebooks = {}
        for i, file_path in enumerate(info_files):
            notebook = ApiInfo(**json.load(open(file_path)))
            notebooks[notebook.name] = notebook
        
        for i,notebook in tqdm(enumerate(notebooks.values()), total=len(notebooks), desc="Processing APIs"):
            # if i < 28: continue
            # if notebook.name == "Search_Flights_Multi_Stops": print(i)
            # continue
            print(f"处理{notebook.name}---inging")
            log_file = os.path.join("/home/snrobot/lin/GraphLinkTools/logss/log2", f'{notebook.name}.log')
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            log = Logger(name=f"logger_{notebook.name}", log_file=log_file, level=logging.DEBUG)
            
            api_name = notebook.name
            # if api_name != "Search_Hotels": continue
            depends_on = []
            #根据api名字获取参数和响应
            res_class = self.apiembedder.query_by_api(api_name)
            
            log.info(f"{api_name}")
            
            params = res_class["params"]
            required_params = [p for p in params if p.get("required") == 1]
            for p in required_params:
                target_api_params = f'{p["native_name"]}:{p["desc"]}'
                log.info(f"{target_api_params}")
                res = self.apiembedder.search_api_response(api_name=api_name, query_vector=[p["desc_embed"]], topk=70)
                res_list = [
                    {item["api_name"]: f"{item['path_name']}: {item['desc']}"} 
                    for item in res[0]
                ]
                log.info(f"retrival:{res_list}")
                
                #res_dict = {api_name:[filed1, field2, ...]}
                depend_p = []
                res_dict = self.get_res_dict(res_list, notebooks)
                log.info(f"res_dict:\n{res_dict}")
                
                for key, value in res_dict.items():
                    target_api_info = self.get_row_api_info(notebook)
                    target_api_params = target_api_info["parameters"]["properties"][p["native_name"]]
                    # print(target_api_params)
                    source_api_info = self.get_row_api_info(notebooks[key])
                    #这里得修改一下
                    api_response_fields_list = [self.get_example(notebooks[key], v.split(":")[0]) for v in value]
                    messages = self.template.response_filter_fine_grained2(target_api_info, target_api_params, source_api_info, Fine_Grained2_Example, api_response_fields_list)
                    log.info(f"messages\n:{json.dumps(messages)}")
                    try:
                        output = self.llm(messages, self.response_format)
                        content = json.loads(strip_json_markdown(output['content']))
                    except Exception as e:
                        # 打印错误信息并跳过当前处理项
                        print.error(f"解析模型输出失败: {e}", exc_info=True)
                        log.error(f"原始输出内容为:\n{output['content']}")
                        continue  # 跳过当前循环，继续下一项
                    #OUTPUT JSON FORMAT:
# [
#     {{
#         "target_api_params": <<target_api_params_name>>,
#         "reason": <<reason>>,
#         "source_jsonpath": <<jsonpath>>,
#         "confidence": <<0-100>>,
#         "dependency_relationship": <<Soft Dependency(Business-association) or Hard Dependency(Prerequisite API) or null>>,
#     }}
# ]
                    
                    log.info(f"{key}---output\n:{content}")
                    for res in content:
                        if not res.get("dependency_relationship", None) or res.get("confidence", 0) < 80:
                            continue
                        res.update(source_api=key)
                        depend_p.append(res)
                
                depends_on.extend(depend_p)
            notebook.update(
                depends_on = depends_on
            )
            self.save_notebook(notebook, self.required_folder, api_name)
    
    # 对res_list进行整合把相同的api名字的字段整合在一起
    def get_res_dict(self, res_list, notebooks):
        res_dict = {}
        
        for item in res_list:
            for key, value in item.items():
                # 提取基础路径（去掉可能的后缀如 ':type'）
                base_path = value.split(':')[0]
                
                # 处理路径获取父节点（跳过以'[]'结尾的路径）
                parent_value = base_path
                if not base_path.endswith('[]'):
                    parent_value = base_path[:base_path.rfind('.')] if '.' in base_path else base_path
                
                # 特殊处理根路径'$'
                if parent_value == '$':
                    response = notebooks[key].responses[0]["observation"]
                    shortened = observation_shorten(response, 2)
                    if count_tokens(shortened) > 5000:
                        parent_value = base_path
                
                # 存储结果（自动去重）
                res_dict.setdefault(key, set()).add(parent_value)
        
        # 过滤出最上层路径
        for key in res_dict:
            paths = sorted(res_dict[key])  # 排序确保短路径优先
            top_level = []
            for path in paths:
                if not any(path.startswith(p + '.') or path == p for p in top_level):
                    top_level.append(path)
            res_dict[key] = set(top_level)
        
        return res_dict
        
    
    
    
    
    
    #对所有的必须参数的依赖进行验证 来获取所有api的响应
    def validate_requried_dependency(self):
        
        info_files = glob.glob(os.path.join(self.api_folder, '*.json'))
        notebooks = {}
        for i, file_path in enumerate(info_files):
            notebook = ApiInfo(**json.load(open(file_path)))
            notebooks[notebook.name] = notebook
        
        notebooks_enhanced = {}
        for notebook in notebooks.values():
            depends_on = notebook.depends_on
            is_verified = notebook.verified
            response = {}
            count = 0
            for param in notebook.docs_row["parameters"]["properties"].values():
                if param.get("required", False):
                    count += 1
            if count == 0: continue
            elif count == 1:
                self.valid_count_one()
            else:
                pass
            
            #对未验证的api进行文档增强
            if not is_verified: 
                pass
        
        #更新api文档
        
        #加入到向量数据库里
        
        return notebooks_enhanced
    
    #对只有一个必须参数的api进行数据依赖验证
    def valid_count_one(self, notebooks, notebook):
        api_name = notebook['name']
        for item in notebook.depends_on:
            break
            
    
    
    #获取jsonpath的例子值
    def get_example(self, notebook, field):
        response = notebook.responses[0]["observation"]
        response = observation_shorten(response, 2)
        field = field.replace("[]", "[*]")
        # expr = f'$.{field}'
        expr = field
        
        
        jsonpath_expr = parse(expr)
        matches = jsonpath_expr.find(response)
        res = [match.value for match in matches]
        res1 = {"field_name": field}
        for i, r in enumerate(res):
            res1.update({f"field_example{i}":r})

        return res1
        
    
    #获取增强后的文档row_doc
    def get_row_api_info(self, notebook):
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
        docs_row_copy["func_description"] = notebook.enhance_func_desc

        return docs_row_copy

    def save_notebook(self, notebook, output_folder, name):
        os.makedirs(output_folder, exist_ok=True)
        file_path = os.path.join(output_folder, f'{name}.json')
        write_file(notebook.to_dict(), file_path)
        
        print(f"Saved to {file_path}")
        
        
    def rules_filter(self,):
        pass
if __name__ == '__main__':
    required_folder = "/home/snrobot/lin/GraphLinkTools/Tools(1)/required_params_link(3)"
    api_info = "/home/snrobot/lin/GraphLinkTools/Tools(1)/required_params_link(2)"
    LinkApideom = LinkApi(required_folder=required_folder, api_info_path=api_info)
    LinkApideom.process_api_required_params()
    
    # api_folder = "/home/snrobot/lin/GraphLinkTools/Tools(1)/ApiInfo_update(1)"
    # info_files = glob.glob(os.path.join(api_folder, '*.json'))
    # notebooks = {}
    # for i, file_path in enumerate(info_files):
    #     notebook = ApiInfo(**json.load(open(file_path)))
    #     notebooks[notebook.name] = notebook
    
    # for name, notebook in notebooks.items():
    #     if not notebook.responses:continue
    #     if name == 'Get_Room_List':continue
    #     responses = notebook.responses[0]["observation"]
    #     response_desc_list = notebook.response_desc_list
    #     for item in response_desc_list:
    #         field = item['path_name']
    #         field = field.replace("[]", "[*]")

            
    #         jsonpath_expr = parse(field)
    #         matches = jsonpath_expr.find(responses)
    #         if not matches:
    #             print(f"{name} has no field {field}")
    #     print(f"Finished,,,{name}")

