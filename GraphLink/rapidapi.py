import json
import requests
import copy
import os
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.utilize import *
from tenacity import retry, stop_after_attempt
from urllib.parse import urlparse
from dotenv import load_dotenv
load_dotenv("/home/snrobot/lin/GraphLinkTools/.env")

class RapidAPICall():
    def __init__(self, tool, tool_info):
        self.remote = True
        self.name_to_url = self.get_name_to_url(tool_info)
        self.path_params = []
        self.tool = tool
        
    @retry(stop=stop_after_attempt(3))
    def _call(self, func_call):
        self.url = self.name_to_url[func_call["name"]]
        host = urlparse(self.url)
        self.headers = {
            "X-RapidAPI-Key": os.getenv("RAPID_API_KEY"),
            "X-RapidAPI-Host": host.netloc
        }
        # self.url = "https://booking-com15.p.rapidapi.com" + self.url
        
        params_copy = copy.deepcopy(func_call['arguments'])
        if params_copy == None:
            return {"fail":{"error": "No arguments provided"}}
        
        param_dict = {}
        for path_param in self.path_params:
            if f"{{{path_param}}}" in self.url and path_param in params_copy:
                param_dict[path_param] = params_copy.pop(path_param)
        self.url = self.url.format(**param_dict)
        # print(self.url)

        # for k, value in params_copy.items():
        #     if k == "legs":
        #         params_copy[k] = json.dumps(value, ensure_ascii=False)
        try:
            # print(params_copy)
            response = requests.get(self.url, headers=self.headers, params=params_copy)
            # print(response.status_code)
        except requests.exceptions.RequestException as e:
            return {"error": "Network Error", "detail": str(e)}
        
        json_response = response.json()
        json_response["http_status_code"] = response.status_code
        # 对Get_Room_Availability结果进行转换
        if "data" in json_response:
            response1 = json_response["data"]
            if func_call["name"] == "Get_Room_Availability":
                response1 = self.transform_get_room_availability(json_response["data"])
            json_response["data"] = response1
        
        return json_response



    def observation_shorten(self, response):
        if response == None:
            return response
    
        if isinstance(response, dict):
            # keys_to_delete = [key for key, value in response.items() if (value in ["", None, {}, []])]
            # for key in keys_to_delete:
            #     response.pop(key)

            for key, value in response.items():
                response[key] = self.observation_shorten(value)
                
        elif isinstance(response, list):
            if len(response) > 3:
                response = response[:3]
            response = [self.observation_shorten(item) for item in response]

        return response
    
    def get_name_to_url(self, tool_info):
        name2url = {tool['name']: tool["endpoint"] for tool in tool_info}
        return name2url
    
    #对Get_Room_Availability结果进行转换
    def transform_get_room_availability(self,original_response):
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


if __name__ == "__main__":
    apis_info_path = "/home/snrobot/lin/GraphLinkTools/Tools(1)/all_apis.json"
    with open(apis_info_path, 'r') as f:
        tool = json.load(f)
    tool_info = tool['functions']
    host = None
    rapidapi = RapidAPICall(tool="booking-com15", tool_info=tool_info)
    # name = "Get_Languages"
    # params = {
        
    # }
    name = "Car_Details"
    params = {
                "vehicleId":"",
                "searchKey":"eyJkcml2ZXJzQWdlIjozMCwiZHJvcE9mZkRhdGVUaW1lIjoiMjAyNS0wNi0xNVQyMzo1OTowMCIsInBpY2tVcERhdGVUaW1lIjoiMjAyNS0wNi0xNFQyMDowMDowMCIsInBpY2tVcExvY2F0aW9uIjoiNDAuNzU5NTksLTczLjk4NDkxIiwicGlja1VwTG9jYXRpb25UeXBlIjoiTEFUTE9ORyIsInJlbnRhbER1cmF0aW9uSW5EYXlzIjoyLCJzZXJ2aWNlRmVhdHVyZXMiOlsiTk9fT1BBUVVFUyIsIlNVUFJFU1NfRklYRURfUFJJQ0VfVkVISUNMRVMiLCJJTkNMVURFX1BST0RVQ1RfUkVMQVRJT05TSElQUyIsIklOQ0xVREVfRVhUUkFTX0NPTlRBSU5JTkdfRkVFUyIsIlNVUFBSRVNTX0RJUkVDVF9QQVlfTE9DQUxfVkVISUNMRVMiXX0="
            }
    response = rapidapi._call({"name":name, "arguments":params})
    print(name)
    print(params)
    print(response)
    # print(type(response))
    # response_required_shorten = rapidapi.shorten_response(response)
    c = count_tokens(response)
    print(c)
    