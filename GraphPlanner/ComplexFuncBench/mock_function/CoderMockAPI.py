import copy
import json
import sys, os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
from ComplexFuncBench.utils.utils import *
from ComplexFuncBench.utils.logger import Logger
from ComplexFuncBench.mock_function.QwenRunner import QwenRunner
class CoderMockAPI:
    def __init__(self, runner, args):
        self.runner = runner
        # 保存每次调用的记录
        self.call_history = []
    def __getattr__(self, func_name):
        def wrapper(*args, **kwargs):
            if args and isinstance(args[0], dict):
                arguments = args[0]
            else:
                arguments = kwargs
            return self.call(func_name, arguments)
        return wrapper

    def call(self, name, arguments):
        # 记录调用历史
        call_record = {"name": name, "arguments": arguments}
        mock_res = self.runner.get_mock_res(call_record) 
        self.call_history.append(call_record)
        # 按你要求，只返回这个，不做任何多余事
        if isinstance(mock_res, dict) and not mock_res.get("status", True):
        # 可选：记录失败日志
            error_msg = mock_res.get("message", "Unknown mock failure")
            raise RuntimeError(f"[Mock API Failed] {name} - {error_msg}")
        if name == 'Get_Room_List_With_Availability':
            return {'status': True, 'message': 'Success', 'data':{'available':mock_res['available'], 'unavailable':mock_res['unavailable']}}
        return mock_res

    def reset(self):
        self.call_history = []

import argparse
import datetime
import os
def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--log_dir", type=str, default="logs/test.log")
    parser.add_argument("--input_file", type=str, default="data/ComplexFuncBench.jsonl")
    parser.add_argument("--model_name", type=str,  choices=[], help="The name of the model to be evaluated.", default="qwen2.5-72b-instruct")
    parser.add_argument('--exp_name', type=str, default='full-1000')
    parser.add_argument("--vllm_url", type=str)
    parser.add_argument("--proc_num", type=int, default=1)
    parser.add_argument("--debug", action="store_true")

    args = parser.parse_args()

    os.makedirs(f"logs/{datetime.date.today().strftime('%Y-%m-%d')}/{args.model_name}", exist_ok=True)
    os.makedirs(f"result/{args.model_name}/{args.exp_name}/logs", exist_ok=True)

    args.log_dir = f"logs/{datetime.date.today().strftime('%Y-%m-%d')}/{args.model_name}/{args.exp_name}.log"
    args.output_dir = f"result/{args.model_name}/{args.exp_name}.jsonl"
    args.log_dir = f"result/{args.model_name}/{args.exp_name}/logs"
    return args

if __name__ == "__main__":
    file = "/home/snrobot/lin/GraphLinkTools/GraphPlanner/ComplexFuncBench/data/ComplexFuncBench.jsonl"
    with open(file, 'r') as f:
        for i, line in enumerate(f):
            if i != 320: continue
            data = json.loads(line)

    args = get_args()
    log_dir = f"{args.log_dir}/{data['id']}.log"
    logger = Logger(f"evaluation_logger_{data['id']}", log_dir, logging.DEBUG)

    # print(type(logger))
    runner = QwenRunner(args, logger, data)
    f = CoderMockAPI(runner, args)
    # params = {'query': 'Chicago, USA'}
    # res1  = f.Search_Flight_Location(params)
    # print(res1)
    # print(type(res1['data']))
    params = {'query': 'Pudong Shangri-La, Shanghai'}
    res = f.Search_Attraction_Location(params)
    print(res)
    
    # res2 = f.Search_Hotels(dest_id = 24194, search_type = "hotel", arrival_date = "2024-11-21", departure_date = "2024-12-08", adults = 1)
    # print(len(res2))

    # res2 = f.Search_Hotels(dest_id = 24194, search_type = "hotel", arrival_date = "2024-11-21", departure_date = "2024-12-08", adults = 1)
    # print(len(res2))

    