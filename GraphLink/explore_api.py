from basellms import DeepSeekRequest, QwenRequest
from rapidapi import RapidAPICall
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from template.Explore_Prompts import ExplorePrompts
import dotenv
import json
import random
import copy
dotenv.load_dotenv("/home/snrobot/lin/GraphLinkTools/.env")

class ToolExplore:
    def __init__(self, apis_info_path, example_path, static_response_path, api_response_path):
        # 加载工具文档
        with open(apis_info_path, 'r') as f:
            tool_info = json.load(f)
        self.tool_info = tool_info['functions']
        self.host = tool_info['host']
        #获取静态response
        self.static_response = self.get_static_response(static_response_path)
        
        
        # 初始化gpt模型 和  rapidapi 接口文件
        params = {
        "model_name": "deepseek-chat",
        "api_key": "sk-f17e647c3ba449e29415f1f64c070ae6",
        "base_url": "https://api.deepseek.com"
    	}
        self.response_format={'type': 'json_object'}
        self.llm = DeepSeekRequest(**params)
        self.rapidapi = RapidAPICall(tool="booking-com15", tool_info=self.tool_info, host=self.host)
        
        # 加载提示词中的例子
        with open(example_path, 'r') as f:
            example = json.load(f)
        self.required_example = self.format_json(example['required_paramers_explore'])
        self.optional_example = self.format_json(example['optional_paramers_explore'])
        # print(self.required_example)
        # 加载提示词
        self.template = ExplorePrompts()
        # 加载输出响应文件
        self.output_file = open(api_response_path, 'a', encoding='utf-8')
    def get_api_response(self, n = 1):

        # 探索API的各种响应并将响应简洁化
        for i , tool in enumerate(self.tool_info):
            # if i >= 1 : break
            name = tool['name']
            # if name != "Get_Seat_Map": continue
            print(name)
            params = tool['parameters']
            #==================================进行两种探索，1.必选参数 ==================================
            messages = self.template.explore_api_by_required(tool_docs = self.format_json(tool), Example=self.required_example)
            # print(messages)
            output = self.llm(messages, self.response_format,)
            # print("=="*20)
            # print(output['content'])
            # print(self.strip_json_markdown(output['content']))
            # print("=="*20)
            content = json.loads(self.strip_json_markdown(output['content']))
            #提取query 和 对应的response
            query_required = content['User Query']
            params_required = content['Parameters']
            params_required = self.clean_params(params, params_required)
            # print(params_required)
            
            # 进行API调用
            response_required = self.rapidapi._call({"name":name, "arguments":params_required})
            response_required_copy = copy.deepcopy(response_required)
            response_required_shorten = self.rapidapi.observation_shorten(response_required)
            # print(response_required)
            # print("**"*20)
            # print(response_required_shorten)
            #2. ==================================可选参数=========================================
            messages = self.template.explore_api_by_optional(tool_docs = self.format_json(tool), Example=self.optional_example, previous_user_query=query_required)
            output = self.llm(messages, self.response_format, )
            # print("=="*20)
            # print(output['content'])
            # print(self.strip_json_markdown(output['content']))
            # print("=="*20)
            content = json.loads(self.strip_json_markdown(output['content']))
            #提取query 和 对应的response
            query_optional = content['User Query']
            params_optional = content['Parameters']
            params_optional = self.clean_params(params, params_optional)
            #调用API
            response_optional = self.rapidapi._call({"name":name, "arguments":params_optional})
            response_optional_copy = copy.deepcopy(response_optional) 
            response_optional_shorten = self.rapidapi.observation_shorten(response_optional)
            
             #3. ==================================从静态数据中提取响应=========================================
            # if response_optional == None and response_required == None:
            static_response_value = self.static_response.get(name)
            static_reponse = self.rapidapi.observation_shorten(random.choice(static_response_value)) if static_response_value else None

            
            record = {
                "shorten":{
                "api":tool,
                "static_response":static_reponse,
                "required": {"query": query_required, "params": params_required, "response": response_required_shorten},
                "optional": {"query": query_optional, "params": params_optional, "response": response_optional_shorten}
            },
                "row":{
                "required":response_required_copy,
                "optional":response_optional_copy
            }}
            
            
            self.save_to_file(name, record)
    
    def expore_params(self, name, ):
        pass
    def save_to_file(self, api_name, record):
        output_dir = "/home/snrobot/lin/GraphLinkTools/Tools/func2"
        os.makedirs(output_dir, exist_ok=True)
        file_path = os.path.join(output_dir, f"{api_name}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(record, f, ensure_ascii=False, indent=4)

        print(f"Saved to {file_path}")
    
    def clean_params(self, params, need_clean_params):
        for param, p_value in params["properties"].items():
            value = need_clean_params.get(param)
            required = p_value.get("required", False)
            if isinstance(value, str) and value.strip().lower() == "i don't know":
                need_clean_params.pop(param)

        return need_clean_params
            
    def get_static_response(self, static_response_path):
        with open(static_response_path, 'r') as f:
            static_response = json.load(f)
        tool_response = {}
        for call in static_response:
            function_name = call["function_name"]
            if function_name not in tool_response:
                tool_response[function_name] = []
            tool_response[function_name].append(call)
            
        return tool_response
    
    def strip_json_markdown(self, text):
        if text.startswith("```"):
            text = text.strip("`").strip()
            if text.startswith("json"):
                text = text[len("json"):].strip()
        return text  
    
    def format_json(self, example):
        example_str = ""
        if isinstance(example, dict):
            example_str = json.dumps(example, ensure_ascii=False, indent=4)
        elif  isinstance(example, list):
            for i, ex in enumerate(example):
                example_str += f"Example{i+1}:\n    {json.dumps(ex, ensure_ascii=False, indent=4)}\n\n"
        return example_str
    

if __name__ == '__main__':
    api_info_path = "/home/snrobot/lin/GraphLinkTools/Tools/Apis(1).json"
    example_path = "/home/snrobot/lin/GraphLinkTools/template/Example.json"
    static_response_path = "/home/snrobot/lin/GraphLinkTools/Tools/Static_Response.json"
    api_response_path = "/home/snrobot/lin/GraphLinkTools/Tools/API_Response.json"
    tooleplore = ToolExplore(api_info_path, example_path, static_response_path, api_response_path)
    
    # tooleplore.clean_params()
    tooleplore.get_api_response()

