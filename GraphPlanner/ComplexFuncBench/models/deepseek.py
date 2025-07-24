from typing import Any, Dict
import os
from openai import OpenAI
import json
import sys
import copy
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
from ComplexFuncBench.prompts.prompts import SimpleTemplatePrompt
from ComplexFuncBench.utils.utils import *


class DeepSeekModel:
    def __init__(self, model_name, api_key, base_url):
        super().__init__()
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = base_url
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def __call__(self, prefix, prompt: SimpleTemplatePrompt, **kwargs: Any):
        filled_prompt = prompt(**kwargs)
        prediction = self._predict(prefix, filled_prompt, **kwargs)
        return prediction

    def _predict(self, prefix, text, **kwargs):
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": prefix},
                {"role": "user", "content": text}
            ],
            'max_tokens': kwargs.get("max_tokens", 8192),
            "temperature": kwargs.get("temperature", 0.0),
            "top_p": kwargs.get("top_p", 0.95),
            "n": kwargs.get("n", 1),
        }


        for i in range(10):
            try:
                start_time = time.time()
                response = self.client.chat.completions.create(**payload, response_format= {
                'type': 'json_object'
            })
                end_time = time.time()

                content = (
                    response.choices[0].message.content
                    if payload["n"] == 1
                    else [choice.message.content for choice in response.choices]
                )
                return content

            except Exception as e:
                print(f"API error (attempt {i+1}/10): {e}")
                time.sleep(30)

        return {
            "content": "no response from DeepSeek model...",
            "time": -1,
            "usage": [0, 0, 0]
        }

if __name__ == "__main__":
    params = {
        "model_name": "deepseek-chat",
        "api_key": "sk-f17e647c3ba449e29415f1f64c070ae6",
        "base_url": "https://api.deepseek.com"
    	}
    response_format={'type': 'json_object'}
    model = DeepSeekModel(**params)
    response = model("You are a helpful assistant.", SimpleTemplatePrompt(template=("What is the capital of France?"), args_order=[]))
    print(response)