import os, sys
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.requests import Request
import uvicorn
import time
import json
import yaml
import requests
from typing import Union
# from utils import standardize, change_name

from fastapi import FastAPI
from slowapi.errors import RateLimitExceeded
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from openai import OpenAI, AzureOpenAI
import re
from system_prompts import SFT_SYSTEM,COT_SYSTEM

# config_file='config_mirrorapi.yml'
# CONFIG = yaml.load(open(config_file, 'r'), Loader=yaml.FullLoader)
# print(CONFIG)


def extract_attributes_json(output):
    # Extract the values
    try:
        output_dict = json.loads(output)
        print(output_dict)
    except:
        print("Error: Invalid JSON format.")
        # Regular expression to capture "error" and "response" fields
        if "mechanism_of_the_api" in output:
            pattern = (
                r'"mechanism_of_the_api"\s*:\s*"(.*?)",\s*'   # Capture mechanism_of_the_api
                r'"error"\s*:\s*"(.*?)",\s*'                 # Capture error
                r'"response"\s*:\s*"(.*)'                    # Capture response (no final quote)
            )
            match = re.search(pattern, output, re.DOTALL)

            if match:
                reason_content = match.group(1)
                error_content = match.group(2)  # Extract error content
                response_content = match.group(3)  # Extract response content
                output_dict = {"error": error_content, "response": response_content}
            else:
                print("No matches found.")
                return None, None, None
        else:
            pattern = r'"error":\s*"([^"]*)",\s*"response":\s*"(.*)'
        # Search for matches
            match = re.search(pattern, output, re.DOTALL)

            if match:
                error_content = match.group(1)  # Extract error content
                response_content = match.group(2)  # Extract response content
                output_dict = {"error": error_content, "response": response_content}
            else:
                print("No matches found.")
                return None, None, None
    error, response = output_dict['error'], output_dict['response']
    return None, error, response



class MirrioGptRequert:
    def __init__(self, model_name=None, api_key=None, base_url=None):
        # self.api_key = api_key if api_key else CONFIG['api_key']
        # self.base_url = base_url if base_url else CONFIG['api_base']
        # self.model_name = model_name if model_name else CONFIG.get('model_name', 'mirrioAPI')

        self.client = OpenAI(
            base_url="http://127.0.0.1:12345/v1/",
            api_key="EMPTY"  # vLLM 没有实际校验，可为任意非空字符串
        )
        response = self.client.chat.completions.create(
            model="qwen2.5",  # 替换为你实际设置的 --served-model-name
            messages=[
                {"role": "user", "content": "hello"}
                ]
        )
        print(response)
    def __call__(
            self,
            tool_input, data, api_doc,
            **kwargs
    ):
        USER_PROMPT = """\
API doc:
{api_doc}

Request:
{request}\
"""
        api_doc = {
        "api_name": api_doc['api_info'][0]['name'],
        "api_description": api_doc['api_info'][0]['description'],
        "required_parameters": api_doc['api_info'][0]['required_parameters'],
        "optional_parameters": api_doc['api_info'][0]['optional_parameters'],
        "tool_description": api_doc['tool_description'],
        "tool_name": data['tool_name'],
        "tool_category": data['category'],
    }
        
        request = {**tool_input}
        instruction = USER_PROMPT.format(api_doc=api_doc, request=request)
        messages = [
            {"role": "system", "content": SFT_SYSTEM},
            {"role": "user", "content": instruction},
        ]
        
        generate_text = self.client.chat.completions.create(
            model="qwen2.5",
            messages=messages,
            temperature=CONFIG['temperature'],
            max_tokens=2048,
            seed=42
        )
        
        generate_text = generate_text.choices[0].message.content
        
        _, error, response = extract_attributes_json(generate_text)
        if error or response:
            return json.dumps({"error": error, "response": response})
        else:
            fake_error = {
                "error": "Failed to generate fake response",
                "response": "",
            }
            return json.dumps(fake_error)

if __name__ == '__main__':
    
    from vllm import LLM, SamplingParams

    # 模型路径（HuggingFace 格式）
    model_path = "/home/snrobot/lin/Llm-model/qwen2.5-7b"

    # 初始化 LLM 引擎
    llm = LLM(
        model=model_path,
        tokenizer=model_path,
        trust_remote_code=False,
        dtype="half",  # 使用 float16 精度
        max_model_len=2048,
        gpu_memory_utilization=0.6,
        tensor_parallel_size=1  # 如果有多个 GPU，可以设置为 GPU 数量
    )

    # 设置采样参数
    sampling_params = SamplingParams(
        temperature=0.1,
        top_p=0.95,
        max_tokens=2048,
    )

    # 输入提示词
    prompts = [
        "你好，请介绍一下你自己。",
        "请告诉我如何做西红柿炒鸡蛋。",
    ]

    # 批量推理
    outputs = llm.generate(prompts, sampling_params)

    # 输出结果
    for output in outputs:
        print(f"Prompt: {output.prompt}")
        print(f"Generated text: {output.outputs[0].text}")
        print("-" * 50)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    # gpt = MirrioGptRequert()
#     tool_input = {
#     "slug": "prg6h2lj9jfx-city-pub-crawl-with-drinks",
#     "date": "2024-09-01",
#     "currency_code": "EUR",
#     "languagecode": "en-us"
# }

#     data = {
#     "tool_name": "Get_Availability",
#     "category": "Attraction"
# }

#     api_doc = {
#     "api_info": [{
#         "name": "Get_Availability",
#         "description": "Check if tickets for tourist attractions are available.",
#         "required_parameters": {
#             "slug": "slug can be retrieved from api/v1/attraction/searchLocation endpoint."
#         },
#         "optional_parameters": {
#             "date": "The availability of the data.",
#             "currency_code": "The currency code.",
#             "languagecode": "To obtain the response data in a specific language."
#         }
#     }],
#     "tool_description": "Check if tickets for tourist attractions are available.",
# }

#     response = gpt(tool_input, data, api_doc)
#     print(response)

    # from openai import OpenAI
    print("hhh")
    client = OpenAI(
        base_url="http://localhost:12345/v1",
        api_key="EMPTY"  # vLLM 没有实际校验，可为任意非空字符串
    )
    response = client.chat.completions.create(
        model="qwen2.5",  # 替换为你实际设置的 --served-model-name
        messages=[
            {"role": "user", "content": "who are you"}
        ]
    )

    print(response.choices[0].message.content)

