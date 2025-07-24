import os,sys
import json
import glob
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ComplexFuncBench.utils.logger import Logger
from ComplexFuncBench.utils.utils import *
from ComplexFuncBench.mock_function import CoderMockAPI
from ComplexFuncBench.mock_function.QwenRunner import QwenRunner
from GraphLink.tool import ApiInfo

from GraphAct_1 import run_single
from act import run, restore_shell_context_as_string


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
    os.makedirs(f"result/{args.model_name}/logs", exist_ok=True)
    os.makedirs(f"result/{args.model_name}/record", exist_ok=True)

    # args.log_dir = f"logs/{datetime.date.today().strftime('%Y-%m-%d')}/{args.model_name}/{args.exp_name}.log"
    args.output_dir = f"result/{datetime.date.today().strftime('%Y-%m-%d')}/{args.model_name}/record"
    args.log_dir = f"result/{datetime.date.today().strftime('%Y-%m-%d')}/{args.model_name}/logs"
    return args
def evaluation(data, args):
    log_dir = f"{args.log_dir}/{data['id']}.log"
    out = f"{args.output_dir}/{data['id']}.json"
    os.makedirs(args.log_dir, exist_ok=True)
    os.makedirs(args.output_dir, exist_ok=True)
    logger = Logger(f"evaluation_logger_{data['id']}", log_dir, logging.DEBUG)

    model_name = args.model_name
    #加载图关系
    api_link_floder = "/home/snrobot/lin/GraphLinkTools/gound_truth/api_link_gt_clean(3).jsonl"
    api_link = json.load(open(api_link_floder, 'r'))
    #加载工具信息
    api_folder_path = "/home/snrobot/lin/GraphLinkTools/GraphPlanner/data/APIinfo_update(3)"
    info_files = glob.glob(os.path.join(api_folder_path, '*.json'))
    notebooks = {}
    for i, file_path in enumerate(info_files):
        notebook = ApiInfo(**json.load(open(file_path)))
        notebooks[notebook.name] = notebook

    logger.info(f"Test Example {data['id']}")
    logger.info(f"Query: {data['conversations'][0]['content']}")
    
    turn_count, call_count = 0, 0
    for turn in data['conversations']:
        if turn['role'] == "assistant" and "function_call" in turn:
            turn_count += 1
            call_count += len(turn["function_call"])
    try:
    #在图上进行遍历
        sub_tasks, tools = run_single(data, model_name, api_link, notebooks)
        #根据遍历的信息 进行coder
        exe_res , correct_count_dict, messages = run(data, args, logger, model_name, sub_tasks, tools)
        shell_context = restore_shell_context_as_string(exe_res)
        result = {
            "id": data['id'], 
            "shell_context": shell_context,
            "messages": messages,
            "count_dict": {
                "total_turn_num": turn_count,
                "correct_call_num": correct_count_dict,
                "total_call_num": call_count,
            },
        }

    except Exception as e:
        result = {
            "id": data['id'], 
            "shell_context": shell_context,
            "messages": messages,
            "count_dict": {
                "total_turn_num": turn_count,
                "correct_call_num": correct_count_dict,
                "total_call_num": call_count,
            },
        }
        logger.error(e)
    finally:
        # 无论如何都写入结果文件
        with open(out, 'a+') as f:
            f.write(json.dumps(result, indent=4, ensure_ascii=False) + "\n")
            f.flush()
    return result
    


def main():
    args = get_args()
    file = "/home/snrobot/lin/GraphLinkTools/GraphPlanner/ComplexFuncBench/data/ComplexFuncBench.jsonl"
    with open(file, 'r') as f:
        data = [json.loads(line) for line in f]
    #隔10个取一个数据
    for i, d in enumerate(data):
        if i < 690:
            continue
        if i % 10 == 0:
            try:
                # if i != 570:
                #     continue
                evaluation(d, args)
            except Exception as e:
                # 记录错误日志，并跳过当前数据
                error_msg = f"Error processing data {d['id']} at index {i}: {str(e)}\n"
                error_msg += "Traceback:\n" + traceback.format_exc()
                print(error_msg)
                continue  # 跳过当前数据，继续执行后续的数据
        


if __name__ == "__main__":
    main()
