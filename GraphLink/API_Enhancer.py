from basellms import DeepSeekRequest, QwenRequest
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.utilize import *
from template.Enhance_Prompts import EnchancePrompts
from tool import ApiInfo
from typing import Union, Dict
from logger import Logger
import logging

import json
import dotenv
import json
import random
import copy
import glob
import pprint
dotenv.load_dotenv("/home/snrobot/lin/GraphLinkTools/.env")

os.environ["TOKENIZERS_PARALLELISM"] = "false"
log = Logger(name="test_logger", log_file="/home/snrobot/lin/GraphLinkTools/logs/test2.log", level=logging.DEBUG)

class APIDocumentationEnhancer:
    def __init__(self, api_folder_path, example_path, output_folder):
        #初始化gpt模块
        params = {
        "model_name": "deepseek-chat",
        "api_key": os.getenv("Deepseek_API_KEY"),
        "base_url": "https://api.deepseek.com"
        }
    #     params = {
    #     "model_name": "deepseek-v3",
    #     "api_key": "sk-f418d022aa7846eda995a61fef80bf85",
    #     "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"
    # }
        self.llm = DeepSeekRequest(**params)
        
        #加载数据文档
        self.info_files = glob.glob(os.path.join(api_folder_path, '*.json'))
        self.notebooks = self.get_api_notebook(self.info_files)
        #加载提示词和例子模板
        with open(example_path, 'r', encoding='utf-8') as f:
            self.example = json.load(f)[0]
        
        
        self.template = EnchancePrompts()
        self.response_format = {'type': 'json_object'}
        #确定响应输出文件
        self.output_folder = output_folder
    def enhance_api_doc(self):
        for i, (name, notebook) in enumerate(self.notebooks.items()):
            
            # if notebook.verified:
            #     shorten_obs = copy.deepcopy(notebook.responses[0]["observation"])
            #     shorten_obs = observation_shorten(shorten_obs, 1)
            #     token_num = count_tokens(shorten_obs)
            #     if token_num < 3000: 
            #         continue
            # if i <= 17: continue
            if name != "Get_Location" : continue
            #<======================================获取api响应的总结===========================>
            if not notebook.verified: 
                print(f"API {name} is not verified, skipping...")
                api_params_desc = self.api_params_rewrite(notebook, response_summary="", api_enchanced_desc="")
                
                notebook.update(
                    enhance_params_desc = api_params_desc,
                )
                
                file_path = os.path.join(self.output_folder, f'{name}.json')
                write_file(notebook.to_dict(), file_path)
                print(f"Saved to {file_path}")
                continue
            
            print(name)
            response_summary = self.api_response_summary(notebook)
            #<==================根据总结对api响应字段进行描述, 由于响应字段太多，需要对其分段处理=================================>
            
            response_fields = self.api_response_fields_desc(name, notebook, response_summary)
            log.info("response_fields:\n")
            log.info(name)
            log.info(response_fields)
            #<==========================根据总结对api描述字段进行重写=============================>
            api_enchanced_desc = self.api_desc_rewrite(notebook, response_summary)
            
            #<===============================根据总结对api参数字段进行重写=====================>
            api_params_desc = self.api_params_rewrite(notebook, response_summary, api_enchanced_desc)
            
            # 更新的ApiInfo
            notebook.update(
                response_summary = response_summary,
                enhance_func_desc = api_enchanced_desc,
                enhance_params_desc = api_params_desc,
                enhance_resfield_desc = response_fields,
            )
            
            os.makedirs(self.output_folder, exist_ok=True)
            file_path = os.path.join(self.output_folder, f'{name}.json')
            write_file(notebook.to_dict(), file_path)
            
            print(f"Saved to {file_path}")
    
    #对api参数字段进行重写
    def api_params_rewrite(self, notebook, response_summary, api_enchanced_desc):
        api_info_copy = copy.deepcopy(notebook.docs_row)
        api_info_copy["func_description"] = api_enchanced_desc
        params_message = self.template.Enchance_API_Params(
            response_summary = response_summary,
            api_info = api_info_copy,
            Example = self.example,
        )
            
        output = self.llm(params_message, self.response_format)
        api_params_desc = json.loads(strip_json_markdown(output["content"]))
        
        return api_params_desc
    
    #对api描述字段进行重写
    def api_desc_rewrite(self, notebook, response_summary):
        api_info_copy = copy.deepcopy(notebook.docs_row)
        api_info_copy["func_description"] = ""
        
        api_message = self.template.Enchance_API_Desc(
            api_info = api_info_copy,
            api_summary = response_summary,
            Example = self.example,
        )
        
        
        output = self.llm(api_message)
        api_enchanced_desc = output["content"]
        
        return api_enchanced_desc
    
    #对api响应字段进行总结
    def api_response_summary(self, notebook):
        summary_messages = self.template.Summary_Response(
                api_resopnse = notebook.responses[0],
                example = self.example
            )
            
        output = self.llm(summary_messages)
        response_summary = output["content"]
        
        return response_summary
    #对api响应字段进行分段处理描述
    def api_response_fields_desc(self, name, notebook, response_summary):
        shorten_obs = copy.deepcopy(notebook.responses[0]["observation"])
        shorten_obs = observation_shorten(shorten_obs, 1)
        token_num = count_tokens(shorten_obs)
        # log.info(json.dumps(shorten_obs, indent=4, ensure_ascii=False))
        if token_num < 3000:
            response_fields = self.get_response_field_one(notebook.responses[0]["observation"], response_summary)
        else:
            response_fields = self.get_response_field_mutil(shorten_obs, response_summary)
            response_fields = {"response_fields": response_fields}
        
        
        return response_fields
            
    def get_api_notebook(self, info_files) -> Dict[str, ApiInfo]:
        def judge(api_res, file_path):
            try:
                status = api_res.get("status") == True
                message = api_res.get("message") == "Success" or api_res.get("message") == "Successful"
                data = api_res.get("data")
            except:
                print(file_path)
            
            if status and message:
                return data
            return None
        
        notebooks = {}
        for i, file_path in enumerate(info_files):
            response = []
            notebook_tmp = json.load(open(file_path, 'r', encoding='utf-8'))
            api_info = notebook_tmp['shorten']["api"]
            api_res_rd = notebook_tmp['shorten']["required"]
            api_res_op = notebook_tmp['shorten']["optional"]
            
            #判断
            rd_judge = judge(api_res_rd["response"], file_path)
            op_judge = judge(api_res_op["response"], file_path)
            
            if rd_judge is not None and rd_judge not in ({},[],"") and "error" not in rd_judge\
                and "bgo_error" not in rd_judge:
                response.append({"function_name": api_info['name'],
                                "arguments":api_res_rd["params"],
                                "observation":rd_judge})
                
            if op_judge is not None and op_judge not in ({},[],"") and "error" not in op_judge\
                and "bgo_error" not in op_judge:
                response.append({"function_name": api_info['name'],
                                "arguments":api_res_op["params"],
                                "observation":op_judge})
                
            if not response and notebook_tmp['shorten']['static_response'] is not None:
                if rd_judge in ({},[],"") or op_judge in ({},[],""):
                    response.append({
                        "function_name": api_info['name'],
                        "arguments": notebook_tmp['shorten']["static_response"]["arguments"],
                        "observation":notebook_tmp['shorten']['static_response']["observation"]["data"]
                        })
            #响应
            is_verified = False
            if response:
                is_verified = True
            
            instances = []
            notebooks[api_info["name"]] = ApiInfo(
                name = api_info["name"],
                docs_row = api_info,
                instance = instances,
                api_idx = i,
                params = api_info["parameters"],
                responses = response,
                verified = is_verified,
            )
            
        return notebooks

    def get_response_field_one(self, response, response_summary):
        feild_message = self.template.Enchance_API_Response(
                Example = self.example,
                api_response = response,
                api_summary = response_summary,
            )
            
        output = self.llm(feild_message, self.response_format)
        # log.debug(output["content"])
        response_fields = json.loads(strip_json_markdown(output["content"]))
        return response_fields
    
    def get_response_field_one1(self, response, response_summary):
        return {"response_fields": response}
    
    def get_response_field_mutil(self, response, response_summary):
        if isinstance(response, list):
            response_sum = []
            for item in response:
                if count_tokens(item) > 3000:
                    sub_dict_field = self.get_response_field_mutil(item, response_summary)
                else:
                    sub_dict_field =  self.get_response_field_one(item, response_summary)["response_fields"]
                    
                response_sum.append(sub_dict_field)
        
        elif isinstance(response, dict):
            dict_response = {}
            str_response = {}
            for name, res_seg in response.items():
                if isinstance(res_seg, (dict, list)) and res_seg not in ("", {}, []):
                    dict_response[name] = res_seg
                else:
                    str_response[name] = res_seg
                    
            response_sum = {}
            for name, res_seg in dict_response.items():
                if count_tokens(res_seg) > 3000:
                    sub_dict_field = self.get_response_field_mutil(res_seg, response_summary)
                else:
                    
                    sub_dict_field =  self.get_response_field_one(res_seg, response_summary)["response_fields"]
                response_sum[name] = sub_dict_field
                
                
            sub_str_response = self.get_response_field_one(str_response, response_summary)["response_fields"]
            response_sum.update(sub_str_response)
        else:
            response_sum = response

        return response_sum
    
    
    def enhance_api_params(self, ):
        api_folder = "/home/snrobot/lin/GraphLinkTools/Tools/ApiInfo"
        info_files = glob.glob(os.path.join(api_folder, '*.json'))
    
        notebooks = {}
        for i, file_path in enumerate(info_files):
            notebook = ApiInfo(**json.load(open(file_path)))
            notebooks[notebook.name] = notebook 
            
        for i, (name, notebook) in enumerate(notebooks.items()):
            # if i <= 17: continue
            # if name != "Search_Flights_Multi_Stops" : continue
            #<======================================获取api响应的总结===========================>
            print(name)
            if notebook.verified: 
                print(f"API {name} is verified, skipping...")
                file_path = os.path.join(self.output_folder, f'{name}.json')
                write_file(notebook.to_dict(), file_path)
                print(f"Saved to {file_path}")
                continue
            response_summary = ""
            
            #<===============================根据总结对api参数字段进行重写=====================>
            api_info_copy = copy.deepcopy(notebook.docs_row)
            params_message = self.template.Enchance_API_Params(
                response_summary = response_summary,
                api_info = api_info_copy,
                Example = self.example,
            )
            
            output = self.llm(params_message, self.response_format)
            api_params_desc = json.loads(strip_json_markdown(output["content"]))
            
            # 更新的ApiInfo
            notebook.update(
                enhance_params_desc = api_params_desc,
            )
            os.makedirs(self.output_folder, exist_ok=True)
            
            file_path = os.path.join(self.output_folder, f'{name}.json')
            
            write_file(notebook.to_dict(), file_path)
            print(f"Saved to {file_path} 修改了{name}参数描述")
if __name__ == "__main__":
    api_folder_path = "/home/snrobot/lin/GraphLinkTools/Tools(1)/func_response"
    example_path = "/home/snrobot/lin/GraphLinkTools/template/Enhance_doc_desc_example.json"
    output_folder = "/home/snrobot/lin/GraphLinkTools/Tools(1)/ApiInfo(1)"
    
    enhancer = APIDocumentationEnhancer(api_folder_path,example_path,output_folder)
    enhancer.enhance_api_doc()
    
            
            
            
            
            
            
            