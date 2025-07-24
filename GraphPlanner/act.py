import sys, os
from io import StringIO
from LLM import *
from action import *
from utils_planner import *
from IPython import InteractiveShell
from typing import Any, Dict, Tuple
from prompt_code import *
import traceback
from prompt1 import *
from ComplexFuncBench.mock_function.CoderMockAPI import *
from utils_planner import *
from IPython.terminal.interactiveshell import TerminalInteractiveShell
codeprompt = CodePrompt()

def restore_shell_context_as_string(shell_context):
    codes = shell_context["code"]
    results = shell_context["result"]
    errors = shell_context["error"]

    output_lines = []

    for idx, code in enumerate(codes):
        output_lines.append(f"In [{idx + 1}]:")
        output_lines.append(code.strip())
        output_lines.append("")  # 空行分隔

        error = errors[idx]
        result = results[idx]

        if error:
            output_lines.append(f"Error [{idx + 1}]:")
            output_lines.append(str(error))
            output_lines.append("")  # 空行分隔

        if result:
            output_lines.append(f"Out [{idx + 1}]:")
            output_lines.append(str(result))
            output_lines.append("")  # 空行分隔

    return "\n".join(output_lines)

# =============== 基础模块：执行 code ===============
import sys
import traceback
from io import StringIO
from typing import Any, Dict, Tuple
from IPython.core.interactiveshell import InteractiveShell

def remove_ansi_colors(text: str) -> str:
    ansi_escape = re.compile(r'\x1b\[[0-9;]*[mK]')
    return ansi_escape.sub('', text)
def run_code(shell: InteractiveShell, code: str) -> Tuple[Any, Dict[str, Any], Dict[str, Any]]:
    old_stdout = sys.stdout
    sys.stdout = mystdout = StringIO()

    error_info = None
    execute_result = None

    try:
        result = shell.run_cell(code, store_history=True)
        output = mystdout.getvalue().strip()
        output = remove_ansi_colors(output)
        output = re.sub(r'-{75}.*', '', output, flags=re.DOTALL).strip()

        # 无论成功失败都尽量保留输出
        execute_result = output
        if isinstance(execute_result, str):
            execute_result = execute_result.splitlines()

        # 如果执行报错，记录 traceback
        if result.error_in_exec:
            tb_list = traceback.extract_tb(result.error_in_exec.__traceback__)
            tb_list = traceback.extract_tb(result.error_in_exec.__traceback__)
            # traceback_info = [{
            #     "file": tb.filename,
            #     "line_number": tb.lineno,
            #     "function": tb.name,
            #     "code": tb.line.strip() if tb.line else None
            # } for tb in tb_list]
            if tb_list:
                last_tb = tb_list[1]
                traceback_info = [{
                    "file": last_tb.filename,
                    "line_number": last_tb.lineno,
                    "function": last_tb.name,
                    "code": last_tb.line.strip() if last_tb.line else None
                }]
            else:
                traceback_info = []
            error_str = f"{type(result.error_in_exec).__name__}: {str(result.error_in_exec)}"
            error_info = {
                "error_message": error_str[:1000],
                "traceback": traceback_info
            }
    finally:
        sys.stdout = old_stdout

    exclude_vars = {
        "args", "logger", "data", "os", "np", "QwenRunner", "CoderMockAPI", "runner", "F",
        "In", "Out", "exit", "quit", "get_ipython", "open"
    }
    all_vars = {
        k: v for k, v in shell.user_ns.items()
        if not k.startswith("_") and k not in exclude_vars
    }

    return execute_result, error_info, all_vars


# =============== 单次 code 生成与执行 ===============
def reset_shell_namespace(shell: InteractiveShell):
    """
    每次清空命名空间，保留 __builtins__。
    """
    keep_keys = {'__builtins__'}
    for key in list(shell.user_ns.keys()):
        if key not in keep_keys:
            del shell.user_ns[key]
def generate_and_run_code(logger, shell, sub_question, tools, model_name, n=10, max_trunc=1000):
    # 收集工具文档信息
    docs = '\n'.join([f"[{i}] {doc}" for i, doc in enumerate(tools, 1)])
    
    # 初始化消息流
    messages = [
        {"role": "system", 'content': CODE_CLASS.format(CODE_EXAMPLE=CODE_EXAMPLE)},
        {"role": "assistant", "content": "Sure, I will generate the functions step-by-step and end up with `print` statement to show myself their execution results."},
        {"role": "user", 'content': CODE_CLASS_USER.format(question=sub_question, related_api_information=docs)},
    ]
    print(f"User: {sub_question}")

    # 初始化记录变量
    valid_codes = []  # 记录有效的代码片段
    valid_exe_result = []  # 记录有效的执行结果
    valid_errors = []  # 记录错误信息
    valid_variables_name = []  # 记录有效的变量名
    valid_variables = {}  # 记录有效变量及其值

    all_codes = []  # 记录所有的代码执行过程
    all_results = []  # 记录所有的执行结果
    all_errors = []  # 记录所有的错误信息
    all_vars = []  # 记录所有的变量

    error_step = 0  # 错误步骤计数器
    try:
        for i in range(n):
            # 生成代码
            code = LLM(
                query=messages,
                model_name=model_name,
                max_tokens=1536,
            )
            code = code.replace("```python", "").replace("```", "")
            messages.append({"role": 'assistant', "content": code})
            print_colored(code, color="green")

            # 执行生成的代码
            execute_result, error_info, all_vars_temp = run_code(shell, code)

            if all_vars:
                last_vars = set(all_vars[-1].keys())
            else:
                last_vars = set()
            current_vars = set(all_vars_temp.keys())
            # 新增的变量
            new_vars = current_vars - last_vars

            # 记录所有的执行过程
            all_codes.append(code)
            all_results.append(execute_result)
            all_errors.append(error_info)
            all_vars.append(all_vars_temp) #记录的累计变量的快照

            #是当前的变量 不是所有todo
            cur_code_valid = any(k.endswith('_response') for k in new_vars)

            if cur_code_valid:
                valid_codes.append(code)
                valid_exe_result.append(execute_result if execute_result else "")
                valid_errors.append(error_info if error_info else "")

                for k in new_vars:
                    valid_variables_name.append(k)
                    valid_variables[k] = all_vars_temp[k]  # 从 all_vars_temp 里取值

            if error_info:
                # 错误发生时处理逻辑
                if not cur_code_valid:
                    error_step += 1

                print_colored(f"错误信息在这里：{error_info}", color="red")

                # 分析错误信息并提供建议
                suggestion = error_analysis(sub_question, code, error_info, tools, model_name)

                if error_step >= 2:
                    # 错误发生超过两次，使用已记录的上下文来生成进一步的分析和建议
                    shell_context = {
                        "code": all_codes,  # 所有代码
                        "result": all_results,  # 所有执行结果
                        "error": all_errors,  # 所有错误信息
                        "variables_name": valid_variables_name,  # 有效变量名
                        "variables": valid_variables,  # 有效变量
                    }
                    context, s = analyze_result(sub_question, shell_context, suggestion, model_name)
                    error_step = 0

                    # 提示用户错误发生次数，并给出改进建议
                    messages.append({"role": 'user', "content": f"""The current bug has already been resolved by analyzing the response. This is a summary of the useful information:\n{s}.\nPlease perform one of the following actions based on this information:\n1. If the facts are already sufficient to answer the user's question, directly print the useful result using print() — do not generate any further logic code.\n2.If you determine that additional API calls are still required, generate the necessary API invocation code accordingly.\n#Output Format:
    ```python
    import necessary lib
    {{code}}
    ```
    #notes: Generated code must be directly executable via InteractiveShell.instance().run_cell(). All step annotations must use # comments. Avoid including non-essential commentary or summaries.
                    """})
                    continue

                # 只有错误发生一次，提供错误信息及建议
                messages.append({"role": 'user', "content": f"""An error {error_info} occurred during code execution. The recommended improvement is:\n {suggestion}.\n1.Do not repeatedly call APIs that have already been successfully executed. You can reuse the previously successfully executed intermediate variables from previous successful executions in the Jupyter / Shell environment. These variables are still valid and available:\n {valid_variables_name}.\n2.Do not write meaningless reassignments such as:from_id = from_id\nOnly rewrite from the point where the error occurred. Do not re-invoke the APIs that were executed successfully before. You can directly use the previously defined variables in new API calls.\n#Output Format:
    ```python
    import necessary lib
    {{code}}
    ```
    #notes: Generated code must be directly executable via InteractiveShell.instance().run_cell(). All step annotations must use # comments. Avoid including non-essential commentary or summaries.
                                """})

            else:
                messages.append({
                    "role": "user",
                    "content": f"{all_results}"
                })
                # 执行成功时直接返回
                return {
                    "code": valid_codes,
                    "result": valid_exe_result,
                    "error": valid_errors,
                    "variables_name": valid_variables_name,
                    "variables": valid_variables,
                }, messages
            
    except Exception as e:
        return {
                    "code": valid_codes,
                    "result": valid_exe_result,
                    "error": valid_errors,
                    "variables_name": valid_variables_name,
                    "variables": valid_variables,
                }, messages
        logger.info(traceback.print_exc())

    # 如果多次失败，返回最后一次执行结果
    return {
        "code": valid_codes,
        "result": valid_exe_result,
        "error": valid_errors,
        "variables_name": valid_variables_name,
        "variables": valid_variables,
    }, messages


# ===============LLM 对每个错误信息进行分析 给出改正意见 ===============
def error_analysis(sub_question, code, error_info, tools, model_name) -> str:
    docs = '\n'.join([f"[{i}] {doc}" for i, doc in enumerate(tools, 1)])
    system_prompt = ERROR_ANALYSIS.format(error_example=error_example)
    user_prompt = ERROR_ANALYSIS_USER.format(
        query=sub_question,
        code=code,
        error_info=error_info,
        api_info=docs
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    out = LLM(messages, model_name)
    return out
# =============== LLM 对每个子任务进行总结 ===============
def subtask_summary(subtask, shell_context, model_name):
    # 恢复交互式 shell 上下文为字符串
    context = restore_shell_context_as_string(shell_context)

    # 根据上下文生成分析消息
    subtask = subtask["question"]
    messages = CodePrompt.subtask_summary(subtask, context)
    out = LLM(messages, model_name)

    # 提取 [Yes/No] 答案
    match = re.search(r"\[(.*?)\]", out)
    result = match.group(1) if match else ""

    # 如果 LLM 判断当前子任务已经满足
    if result.lower() == "yes":
        return context, out

    # 如果没有满足，尝试让 LLM 选择相关变量
    messages = CodePrompt.select_variable(subtask, context, out, shell_context["variables_name"])
    out = LLM(messages, model_name)

    # 解析 LLM 返回的变量名
    res = json.loads(prase_json_from_response(out))

    # 只保留有效的、且以 _result 结尾的变量
    res_clean = [r for r in res if r in shell_context["variables_name"] and r.endswith("_response")]

    # 针对每个有效变量，继续让 LLM 分析其内容
    outputs = []
    for r in res_clean:
        variable_value = shell_context["variables"].get(r)
        messages = CodePrompt.anaylsis_result(subtask, context, out, variable_value)
        analysis_out = LLM(messages, model_name)
        outputs.append(analysis_out)

    # 拼接所有分析结果
    s = "\n".join(outputs)
    return context, s

# 针对每个有效变量，继续让 LLM分析其内容
def analyze_result(subtask, shell_context, suggestion, model_name):
    context = restore_shell_context_as_string(shell_context)
    subtask = subtask["question"]
    messages = codeprompt.select_variable(subtask, context, suggestion, shell_context["variables_name"])
    out = LLM(messages, model_name, json=1)

    # 解析 LLM 返回的变量名
    res = prase_json_from_response(out)

    # 只保留有效的、且以 _response 结尾的变量
    res_clean = [r for r in res if r in shell_context["variables_name"] and r.endswith("_response")]

    # 针对每个有效变量，继续让 LLM 分析其内容
    try:
        outputs = []
        for r in res_clean:
            variable_value = shell_context["variables"].get(r, "not found")
            messages = codeprompt.anaylsis_result(subtask, context, {r : variable_value})
            analysis_out = LLM(messages, model_name)
            outputs.append(analysis_out)

        # 拼接所有分析结果
        s = "\n".join(outputs)
        return context, s
    except Exception as e:
        logger.info(traceback.print_exc())
    
    

# =============== 总控模块： ===============
def run(data, args, logger, model_name, sub_questions, tools, code =None):
    # #初始化shell的沙盒
    # file = "/home/snrobot/lin/GraphLinkTools/GraphPlanner/ComplexFuncBench/data/ComplexFuncBench.jsonl"
    # with open(file, 'r') as f:
    #     for i, line in enumerate(f):
    #         if i != 700: continue
    #         data = json.loads(line)

    # args = get_args()
    # log_dir = f"{args.log_dir}/{data['id']}.log"
    # logger = Logger(f"evaluation_logger_{data['id']}", log_dir, logging.DEBUG)

    shell = TerminalInteractiveShell()

    # 这是单例模式 不行
    # shell = InteractiveShell.instance()
    shell.user_ns["args"] = args
    shell.user_ns["logger"] = logger
    shell.user_ns["data"] = data

    # 初始化 shell导入包
    result = shell.run_cell("""
                            import os
                            from ComplexFuncBench.mock_function.QwenRunner import QwenRunner
                            from ComplexFuncBench.mock_function.CoderMockAPI import CoderMockAPI
                            runner = QwenRunner(args, logger, data)
                            F = CoderMockAPI(runner, args)
                            """)
    # a,b,c = run_code(shell, code)
    # print(a)
    # print(b)
    # print(c)
    # exit()
    # # # summaries = []  # 存储每个子任务的总结
    # # # questions = []  # 存储每个子任务的提问内容
    # # runner = shell.user_ns["runner"]
    # # correct_id = runner.correct_count_dict
    # # print(correct_id)
    
    # exit()
    shell_context, messages = generate_and_run_code(
        logger=logger,
        shell=shell,
        sub_question=sub_questions,
        tools=tools,
        model_name=model_name,
        n=7,
    )
    runner = shell.user_ns["runner"]
    correct_count_dict = runner.correct_count_dict
    return shell_context, correct_count_dict, messages
    


if __name__ == '__main__':
    # print(codeprompt.anaylsis_result("", "", "", ""))
    # exit()
    dir = '/home/snrobot/lin/GraphLinkTools/GraphPlanner/tmp/output_results_400.json'
    with open(dir, 'r') as f:
        data = json.load(f)
    tools = data['tools']
    sub_tasks = data['sub_tasks']
    model_name = "qwen2.5-72b-instruct"
    code="""
# Step 1: Search for the location ID of Manchester
search_location_params = {
    "query": "Manchester"
}
manchester_location_response = F.Search_Attraction_Location(search_location_params)

# Check API response status
if not manchester_location_response.get('status'):
    raise Exception(f"Search_Attraction_Location failed: {manchester_location_response.get('message', 'Unknown error')}")

# Extract the location ID
location_id = manchester_location_response['data']['destinations']['idx']

# Step 2: Search for the most trending attractions in Manchester
search_attractions_params = {
    "id": location_id,
    "sortBy": "trending",
    "page": "1"
}
attractions_response = F.Search_Attractions(search_attractions_params)

# Check API response status
if not attractions_response.get('status'):
    raise Exception(f"Search_Attractions failed: {attractions_response.get('message', 'Unknown error')}")

# Extract the most trending attractions
trending_attractions = attractions_response['data']['products']

# Print the most trending attractions
print("Most trending tourist spots in Manchester for a family trip:")
for attraction in trending_attractions:
    print(f"- {attraction['name']} (Rating: {attraction['reviewsStats']['combinedNumericStats']['average']}/5, Reviews: {attraction['reviewsStats']['allReviewsCount']})")
"""
    run(data = 0, args= 0, logger= 0, model_name=model_name, sub_questions=sub_tasks, tools=tools, code=code)






        

        
        
        





        


        
