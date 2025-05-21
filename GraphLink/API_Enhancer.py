from basellms import DeepSeekRequest, QwenRequest
from template.Enhance_Prompts import EnchancePrompts
from tool import ApiInfo

import json
import dotenv
import json
import random
import copy,os
import glob
dotenv.load_dotenv("/home/snrobot/lin/GraphLinkTools/.env")



class APIDocumentationEnhancer:
    def __init__(self, api_folder_path, example_path):
        #初始化gpt模块
        params = {
        "model_name": "deepseek-chat",
        "api_key": os.getenv("DEEPSEEK_API_KEY"),
        "base_url": "https://api.deepseek.com"
        }
        self.llm = DeepSeekRequest(**params)
        
        #加载数据文档
        self.info_files = glob.glob(os.path.join(api_folder_path, '*.json'))
        self.notebooks = self.get_api_notebook(self.info_files)
        #加载提示词和例子模板
        with open(example_path, 'r', encoding='utf-8') as f:
            self.example = json.load(f)
        
        
        self.template = EnchancePrompts()
        self.response_format = {'type': 'json_object'}
        #确定响应输出文件
        self.output_path = None
    def enhance_api_doc(self):
        for name, notebook in self.notebooks.items():
            #获取api响应的总结
            if not notebook.is_verified: continue
            
            example = {"response":self.example[0]['response'], 
                       "summary":self.example[0]['response_summary']}
            summary_messages1 = self.template.Summary_Response(
                api_resopnse = notebook.responses[0],
                example = example
            )
            output = self.llm(summary_messages1)
            response_summary = output["content"]
            #根据总结对api进行描述重写
            
            
            
            
            
    
    def revise_api_desc(self):
        pass
            
    def revise_api_params(self):
        pass
    def add_api_response(self,):
        pass
        
    
    def get_api_notebook(self, info_files):
        def judge(api_res):
            status = api_res.get("status") == True
            message = api_res.get("message") == "Success"
            data = api_res.get("data")
            
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
            rd_judge = judge(api_res_rd["response"])
            op_judge = judge(api_res_op["response"])
            
            if rd_judge is not None and rd_judge not in ({},[],"") and "error" not in rd_judge:
                response.append({"function_name": api_info['name'],
                                "arguments":api_res_rd["params"],
                                "observation":rd_judge})
                
            if op_judge is not None and op_judge not in ({},[],"") and "error" not in op_judge:
                response.append({"function_name": api_info['name'],
                                "arguments":api_info["params"],
                                "observation":op_judge})
                
            if not response and notebook_tmp['shorten']['static_response'] is not None:
                if rd_judge in ({},[],"") and op_judge in ({},[],""):
                    response.append(notebook_tmp['shorten']['static_response'])
            #响应
            is_verified = False
            if not response:
                is_verified = True
            
            instances = []
            notebooks[api_info["name"]] = ApiInfo(
                name = api_info["name"],
                docstring = api_info,
                instance = instances,
                api_idx = i,
                params = api_info["parameters"],
                responses = response,
                verified = is_verified,
            )
            
        return notebooks
            

if __name__ == "__main__":
    example = "/home/snrobot/lin/GraphLinkTools/Tools/func2/Get_Hotel_Facilities.json"
    
            
            
            
            
            
            
            