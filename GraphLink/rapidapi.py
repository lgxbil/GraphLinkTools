import json
import requests
import copy
import os
import random
from tenacity import retry, stop_after_attempt
from dotenv import load_dotenv
load_dotenv("/home/snrobot/lin/GraphLinkTools/.env")

class RapidAPICall():
    def __init__(self, tool, tool_info, host):
        self.remote = True
        self.name_to_url = self.get_name_to_url(tool_info)
        self.headers = {
            "X-RapidAPI-Key": os.getenv("RAPID_API_KEY"),
            "X-RapidAPI-Host": host
        }
        print(self.headers)
        self.path_params = []
        self.tool = tool
        
    @retry(stop=stop_after_attempt(3))
    def _call(self, func_call):
        self.url = self.name_to_url[func_call["name"]]
        self.url = "https://booking-com15.p.rapidapi.com" + self.url
        
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
        except requests.exceptions.RequestException as e:
            return {"error": "Network Error", "detail": str(e)}
        return response.json()

        if response.status_code == 200:
            # print("Request success.")
            response = response.json()
            if response['status'] == True:
                if "timestamp" in response:
                    response.pop("timestamp")
                if "data" in response:
                    response = response['data']
            else:
                if "message" in response:
                    return {"fail": response['message']}
        
        return {"success":response}


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


if __name__ == "__main__":
    apis_info_path = "/home/snrobot/lin/GraphLinkTools/Tools/Apis(1).json"
    with open(apis_info_path, 'r') as f:
        tool = json.load(f)
    tool_info = tool['functions']
    host = tool['host']
    rapidapi = RapidAPICall(tool="booking-com15", tool_info=tool_info, host=host)
    name = "Search_Flights_Multi_Stops"
    params = {
                "legs": "[{'fromId':'BOM.AIRPORT','toId':'AMD.AIRPORT','date':'2025-05-25'},{'fromId':'AMD.AIRPORT','toId':'BOM.AIRPORT','date':'2025-05-28'}]"
            }
    response = rapidapi._call({"name":name, "arguments":params})
    # response_required_shorten = rapidapi.shorten_response(response)
    print(response)