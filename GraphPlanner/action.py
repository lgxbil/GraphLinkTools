from LLM import *
import subprocess
from IPython import InteractiveShell
import traceback
from typing import Tuple, Union, Dict, Any


def Code(shell, #传入shell对象
        cum_apt, sub_question, graph_thought, model_name):
    def run_code(code: str) -> Tuple[Union[str, Any], Union[None, Dict[str, Any]]]:
        """
        执行代码并返回执行结果和结构化错误信息
        
        Args:
            code: 要执行的Python代码字符串
            
        Returns:
            tuple: (execute_result, error_info)
                - execute_result: 代码的stdout输出或显式返回值（优先stdout）
                - error_info: 如果出错则为字典格式 {
                    'type': 异常类型名称,
                    'message': 异常消息,
                    'traceback': 格式化调用栈字符串
                }；未出错时返回None
        """
        # 执行代码
        result = shell.run_cell(code, store_history=True)
        
        # 初始化返回数据
        execute_result = None
        error_info = None

        # 1. 获取执行结果（优先stdout，其次返回值）
        if result.stdout:
            execute_result = result.stdout.strip()
        elif result.result is not None:
            execute_result = result.result

        # 2. 处理错误信息（含调用栈）
        if result.error_in_exec:
        # 直接使用traceback的完整输出（已包含类型和消息）
            error_info = {
                'traceback': ''.join(
                    traceback.format_exception(
                        type(result.error_in_exec),
                        result.error_in_exec,
                        result.error_in_exec.__traceback__
                    )
                ).strip()
            }

        return execute_result, error_info
    

def summary():
    pass


def GraphPlanner():
    pass

def ResultParse():
    pass

def summary():
    pass


