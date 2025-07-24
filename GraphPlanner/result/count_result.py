import json
import glob
import os
dir = "/home/snrobot/lin/GraphLinkTools/GraphPlanner/result/qwen2.5-72b-instruct/record"

info_files = glob.glob(os.path.join(dir, '*.json'))
total = 0
myt = 0

# success = 0
# c = 0
# for f in info_files:
#     with open(f, 'r') as f:
#         data = json.load(f)
#         correct_call_num = data['count_dict']['correct_call_num']
#         if correct_call_num:
#             my = len(list(correct_call_num.keys()))
#             actual = data['count_dict']['total_call_num']
#         if my == actual:
#             success += 1
#         total += actual
#         myt += my
#         if actual == my:
#             c += 1
# print(c)
# print(myt / total)
# print(success / len(info_files))
# print(len(info_files))

# exit()
import re
from collections import defaultdict

domains = ['Hotels', 'Flights', 'Car', 'Attraction', 'Cross']
success_call = [0] * len(domains)  # 成功调用次数
success_data = [0] * len(domains)
total_call = [0] * len(domains)    # 总调用次数（如需）

def count_unique_success_calls(log_file_path):
    # 存储不重复的调用记录（用字符串形式存储，方便去重）
    unique_calls = set()

    # 正则匹配成功调用的日志行（示例匹配 "Success matched:" 开头的行）
    success_pattern = re.compile(r"Success matched: \[(.*?)\]")

    with open(log_file_path, 'r', encoding='utf-8') as file:
        for line in file:
            # 检查是否包含成功调用记录
            match = success_pattern.search(line)
            if match:
                # 提取调用的 API 名称和参数（如 {'name': 'X', 'arguments': {...}}）
                call_data = match.group(1)
                unique_calls.add(call_data)  # 自动去重
    return len(unique_calls)

def count_res(data_dict):
    domain = ['Hotels', 'Flights', 'Car', 'Attraction', 'Cross', 'ALL']
    dir = "/home/snrobot/lin/GraphLinkTools/GraphPlanner/result/2025-07-24/qwen2.5-72b-instruct/logs"

    sample_data = 0
    log_files = glob.glob(os.path.join(dir, '*.log')) 
    for file_path in log_files:
        # 根据文件名判断领域（不区分大小写）
        domain_index = -1
        for i, domain in enumerate(domains):
            if domain.lower() in file_path.lower():
                domain_index = i
                break
        
        if domain_index == -1:
            print(f"Warning: Unknown domain in file {file_path}")
            continue

        # 统计并存储
        success_count = count_unique_success_calls(file_path)
        success_call[domain_index] += success_count

        filename = os.path.basename(file_path)  # 获取文件名（带后缀），如 "Attraction-0.log"
        filename_without_ext = os.path.splitext(filename)[0]  # 去掉后缀，如 "Attraction-0"

        call_count = 0
        data = data_dict[filename_without_ext]
        for turn in data['conversations']:
            if turn['role'] == "assistant" and "function_call" in turn:
                call_count += len(turn["function_call"])
        total_call[domain_index] += call_count

        if(success_count == call_count):
            success_data[domain_index] += 1
        

    print("\n=== 调用统计结果 ===")
    for i, domain in enumerate(domains):
        success = success_call[i]
        total = total_call[i]
        if total > 0:
            success_rate = (success / total) * 100
            print(f"{domain}: 成功调用 = {success}, 总调用 = {total}, 成功率 = {success_rate:.2f}%")
        else:
            print(f"{domain}: 成功调用 = {success}, 总调用 = {total}, 成功率 = N/A (无调用)")
    
    sum(success_call)
    sum(total_call)
    print(f"总成功调用 = {sum(success_call)}, 总调用 = {sum(total_call)} 成功率 = {(sum(success_call) / sum(total_call)) * 100:.2f}%")
    print(sample_data)
    print(f"样本通过率 {success_data}")

domains = ['Hotels', 'Flights', 'Car', 'Attraction', 'Cross']
success_call = [0] * len(domains)  # 成功调用次数
success_data = [0] * len(domains)
total_call = [0] * len(domains)    # 总调用次数（如需）

def count_res():
    dir = "/home/snrobot/lin/GraphLinkTools/GraphPlanner/result/2025-07-24/qwen2.5-72b-instruct/record"
    files = glob.glob(os.path.join(dir, '*.json')) 
    for file_path in files:
        domain_index = -1
        for i, domain in enumerate(domains):
            if domain.lower() in file_path.lower():
                domain_index = i
                break
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                count_dict = data['count_dict']
                success_call[domain_index] += len(count_dict['correct_call_num'].keys())
                total_call[domain_index] += count_dict['total_call_num']
                if len(count_dict['correct_call_num'].keys()) == count_dict['total_call_num'] or \
                    len(count_dict['correct_call_num'].keys()) == count_dict['total_call_num'] - 1:
                    success_data[domain_index] += 1
                if len(count_dict['correct_call_num'].keys()) == count_dict['total_call_num'] - 1:
                    print(file_path)
        except:
            print(file_path)
    for i, domain in enumerate(domains):
        success = success_call[i]
        total = total_call[i]
        if total > 0:
            success_rate = (success / total) * 100
            print(f"{domain}: 成功调用 = {success}, 总调用 = {total}, 成功率 = {success_rate:.2f}%")
        else:
            print(f"{domain}: 成功调用 = {success}, 总调用 = {total}, 成功率 = N/A (无调用)")
    sum(success_call)
    sum(total_call)
    print(f"总成功调用 = {sum(success_call)}, 总调用 = {sum(total_call)} 成功率 = {(sum(success_call) / sum(total_call)) * 100:.2f}%")
    print(f"样本通过率 {success_data}")
    


if __name__ == "__main__":
    # file = "/home/snrobot/lin/GraphLinkTools/GraphPlanner/ComplexFuncBench/data/ComplexFuncBench.jsonl"
    # with open(file, 'r') as f:
    #     data = [json.loads(line) for line in f]
    # data_dict = {d['id']: d for d in data}
    # # 使用示例
    # count_res(data_dict)
    count_res()
    