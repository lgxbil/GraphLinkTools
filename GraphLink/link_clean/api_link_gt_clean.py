import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.utilize import *
from typing import Union, Dict,List
from logger import Logger
from basellms import DeepSeekRequest, QwenRequest

import logging
from jsonpath_ng import jsonpath, parse
import json
import dotenv

import random
import copy
import glob,pickle
dotenv.load_dotenv("/home/snrobot/lin/GraphLinkTools/.env")

def gt_link_clean(gt_link_file, out_file):
    file = open(gt_link_file, 'r')
    data = json.load(file)
    
    # LLM 初始化
    response_format = {'type': 'json_object'}
    params = {
        "model_name": "deepseek-chat",
        "api_key": os.getenv("Deepseek_API_KEY"),
        "base_url": "https://api.deepseek.com"
    }
    deepseek = DeepSeekRequest(**params)
    # 获取api信息
    api_folder = "/home/snrobot/lin/GraphLinkTools/Tools/ApiInfo_update(1)"
    info_files = glob.glob(os.path.join(api_folder, '*.json'))
    notebooks = {}
    for i, file_path in enumerate(info_files):
        notebook = ApiInfo(**json.load(open(file_path)))
        notebooks[notebook.name] = notebook

    # 清洗link
    for i, (api_name, params) in tqdm(enumerate(data.items()), total=len(data)):
        # if api_name != "Search_Hotels": continue
        cleaned_param_links = {}
        target_api_name = f"{api_name} description: {notebooks[api_name].docs_row['func_description']}"

        for param_name, link in params.items():
            cur_len = len(link)

            #添加描述
            for item in link:
                source_api = item["source_api"]
                if source_api == 'query':continue
                source_api_description = notebooks[source_api].docs_row['func_description']
                new_source_api_str = f"{source_api} description: {source_api_description}"
                
                # 更新 source_api 字段或进行其他操作
                item["source_api"] = new_source_api_str

            target_api_params = param_name
            links = link

            user = f"""
Target API:
{target_api_name}
Target API Params:
{target_api_params}
Link:
{links}
Output:
"""
            # print(user)
            messages = [
                {"role": "system","content": link_api_template},
                {"role": "user","content":  user},
            ]
            out = deepseek(messages, response_format)
            res = json.loads(strip_json_markdown(out['content']))
            # print(res)
            valid_count = sum(1 for item in res if item.get('is_valid') or item.get('is_valid') == "candidate")
            if cur_len != valid_count:
                print(f"{api_name} {param_name} {cur_len} {valid_count}")
            cleaned_param_links[param_name] = res
        data[api_name] = cleaned_param_links
    
    with open(out_file, 'w') as f:
        json.dump(data, f, indent=4)






link_api_template = f"""
#You are an experienced API interface analyst. Please help me complete the following tasks.

##Task
Strictly check the rationality between the output fields of the source API and the parameter fields of the target API, need to evaluate the following two points:
1. Data semantics match (whether the field meanings are consistent)
2. Cross-business domain is reasonable (whether there is a logical association in business scenarios)

##Rules

1. A valid cross-domain scenario must meet **at least one** of the following:
    - There is a **geographical association** (e.g., attraction → hotel)
    - There is **temporal continuity** (e.g., flight date → hotel date)
    - There is a **user behavior association** (e.g., hotel checkout → taxi pickup)

2. Semantic consistency takes priority. However:
    - If **semantics are not strictly equal**, but the **source field strongly implies or influences the target**, and it is **commonly observed in user scenarios**, the mapping can still be considered **valid**.
    - This is called a **behavior-driven soft mapping**.

3. For behavior-driven soft mappings to be valid, one of the following must apply:
    - The source field **frequently determines** or **implicitly suggests** the target value (e.g., checkout time used as pick-up time).
    - The association is **well-supported by user workflows** in real applications (e.g., searching hotels near a tourist spot).

4. Use the following judgment outputs:
    - `is_valid: true` — strong semantic or business association
    - `is_valid: false` — no reliable link
    - `is_valid: "candidate"` — weak semantic, but plausible business behavior link (behavior-driven soft mapping)

##Example
Target API:
"Search_Hotels"
Target API Params:
"adults" 
Link:
[
    {{
        "target_params_value": 4,
        "target_api_params": "adults",
        "source_api": "Search_Attractions",
        "source_jsonpath": "$.products[2].reviewsStats.combinedNumericStats.total",
        "source_jsonpath_value": 4
    }},
    {{
        "target_params_value": 6,
        "target_api_params": "adults",
        "source_api": "query",
        "source_jsonpath": null,
        "source_jsonpath_value": null
    }},
]
Output:
[
    {{
        "target_api_params": "adults",
        "source_api": "Search_Attractions",
        "source_api_respath": "$.products[2].reviewsStats.combinedNumericStats.total",
        "reason": "The total number of reviews in the review statistics of a travel attraction item has **no relation** to the "number of people" parameter required for hotel searches.",
        "is_valid": false
    }},
    {{
        "target_api_params": "adults",
        "source_api": "query",
        "source_api_respath": null,
        "reason": "The number of people for the hotel is often provided in the user's query",
        "is_valid": true
    }}
]

Target API:
"Search_Car_Rentals"
Target API Params:
"drop_off_time" 
Link:
[
    {{
        "target_params_value": "15:00",
        "target_api_params": "drop_off_time",
        "source_api": "Search_Hotels_By_Coordinates",
        "source_jsonpath": "$.result[0].checkin.from",
        "source_jsonpath_value": "15:00"
    }}
]
Outputs:
[
    {{
        "target_api_params": "drop_off_time",
        "source_api": "Search_Hotels_By_Coordinates",
        "source_api_respath": "$.result[0].checkin.from",
        "reason": "The hotel check-in time (e.g., 15:00) is not semantically equivalent to the car rental drop-off time. However, users often return rental cars right before checking in at a hotel, so this is a plausible behavior-driven mapping.",
        "is_valid": "candidate"

    }}
]


##Output 
[
    {{
        "target_api_params": "xxx",
        "source_api": "xxx",
        "source_api_respath": "xxx",
        "reason": "xxx",
        "is_valid":true/false/ 
    }}
]
"""





if __name__ == "__main__":
    gt_link_file = "/home/snrobot/lin/GraphLinkTools/gound_truth/api_link_gt(5).jsonl"
    output_file = "/home/snrobot/lin/GraphLinkTools/gound_truth/api_link_gt_clean(2).jsonl"
    gt_link_clean(gt_link_file, output_file)