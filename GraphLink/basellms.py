import time
from openai import OpenAI
from typing import Union

class BaseRequest:
    def __init__(self, model_name):
        self.model_name = model_name
        self.usage = []
        self.client = OpenAI(api_key='', base_url='')

    def generate(self,
                 messages=None,
                 stop=None,
                 max_len=1000,
                 temp=1,
                 n=1,
                 **kwargs):
        ...
    def __call__(self, *args, **kwargs):
        ...


class DeepSeekRequest(BaseRequest):
    def __init__(self, model_name, api_key, base_url):
        super().__init__(model_name)
        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model_name
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def __call__(
            self,
            messages=None,
            stop=None,
            max_tokens=8192,
            min_tokens=16,
            temp=0.9,
            top_p=0.95,
            n=1,
            **kwargs
    ):
        payload = {
            "model": self.model_name,
            "messages": messages,
            'max_tokens': max_tokens,
            "temperature": temp,
            "n": n, 
            # 'stop': stop,
            "top_p": top_p,
        }
        # deepseek的json是response_format={'type': 'json_object'}
        payload.update(kwargs)
        
        # print(payload)

        for i in range(10):
            try:
                begin = time.time()
                response = self.client.chat.completions.create(**payload)
                end = time.time()
                cost = end - begin
                
                # 处理响应内容
                content = response.choices[0].message.content if n == 1 else [res.message.content for res in response.choices]
                
                results = {
                    "content": content,
                    "time": cost,
                    "usage": [response.usage.completion_tokens, 
                             response.usage.prompt_tokens, 
                             response.usage.total_tokens]
                }
                return results
            except Exception as e:
                print(f"API error (attempt {i+1}/10):", str(e))
                time.sleep(30)
        
        return {
            "content": 'no response from DeepSeek model...', 
            "time": -1, 
            "usage": [0, 0, 0]
        }

class QwenRequest(BaseRequest):
    def __init__(self, model_name, api_key, base_url):
        super().__init__(model_name)
        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model_name
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def __call__(
            self,
            messages=None,
            stop=None,
            max_tokens=8192,
            min_tokens=16,
            temp=0.9,
            top_p=0.95,
            n=1,
            **kwargs
    ):
        payload = {
            "model": self.model_name,
            "messages": messages,
            'max_tokens': max_tokens,
            "temperature": temp,
            "n": n, 
            # 'stop': stop,
            "top_p": top_p,
        }
        # deepseek的json是response_format={'type': 'json_object'}
        payload.update(kwargs)
        
        
        
        # print(payload)

        for i in range(10):
            try:
                begin = time.time()
                response = self.client.chat.completions.create(**payload)
                end = time.time()
                cost = end - begin
                
                if "stream" in payload and payload["stream"]:
                    content = ""
                    print("流式输出内容为：")
                    for chunk in response:
                        # 如果stream_options.include_usage为True，则最后一个chunk的choices字段为空列表，需要跳过（可以通过chunk.usage获取 Token 使用量）
                        if chunk.choices:
                            delta = chunk.choices[0].delta
                            if delta.content is not None:
                                content += delta.content
                else:
                # 处理响应内容
                    content = response.choices[0].message.content if n == 1 else [res.message.content for res in response.choices]
                    
                results = {
                    "content": content,
                    "time": cost,
                    # "usage": [response.usage.completion_tokens, 
                    #         response.usage.prompt_tokens, 
                    #         response.usage.total_tokens]
                }
                return results
            except Exception as e:
                print(f"API error (attempt {i+1}/10):", str(e))
                time.sleep(30)
        
        return {
            "content": 'no response from DeepSeek model...', 
            "time": -1, 
            "usage": [0, 0, 0]
        }
    
if __name__ == '__main__':
    # params = {
    #     "model_name": "deepseek-chat",
    #     "api_key": "sk-f17e647c3ba449e29415f1f64c070ae6",
    #     "base_url": "https://api.deepseek.com"
    # }
    # gpt = DeepSeekRequest(**params)
    # messages = [
    #     {
    #         "role": "user",
    #         "content": "What is the capital of France?"
    #     }
    # ]
    # out_ = gpt(messages=messages)
    # print(out_)
    params = {
        "model_name": "qwen3-235b-a22b",
        "api_key": "sk-f418d022aa7846eda995a61fef80bf85",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"
    }
    gpt = QwenRequest(**params)
    messages = [
        {
            "role": "user",
            "content": "What is the capital of France?"
        }
    ]
    out_ = gpt(messages=messages, stream=True, extra_body={"enable_thinking": False})
    print(out_)