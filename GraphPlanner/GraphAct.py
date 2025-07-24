import json
import argparse
import os, sys
from collections import deque
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from act import *
import traceback
from GraphLinkTools.GraphPlanner.utils_planner import *
from prompt import *
from memory import *
import concurrent.futures as cf
from GraphLink.basellms import DeepSeekRequest, QwenRequest
from utils.utilize import *
from LLM import *

class node:
    pass
def run_single(data, model_name, api_link):
    '''
    api_link: dict => (item : api_name :{})
    '''
    Graph = []
    try:
        convs, functions = data['conversations'], data['functions']
        query = convs[0]['content']
        print("改写问题...")
        '''
        对问题进行预处理
        '''
        ### 改写问题
        for _ in range(3):
            try:
                query_rewrite_prompt = QUESATION_REWRITE.format(question=query)
                query_rewrite_answer = LLM(query_rewrite_prompt, model_name)
                query_rewrite_response = strip_json_markdown(query_rewrite_answer)
                new_question = query_rewrite_response["written question"]
                break
            except:
                new_question = query
        new_question1 = f"User original query: {query}nThe following is a rewrite to help you understand (if the rewrite conflicts with the original content, please follow the original content):\n{new_question}"
        print(new_question1)

        ### 工具选取和子工具过滤 需要处理一下tool的格式 todo
        used_tools = functions
        # 子工具选择LLM
        # used_sub_tools = filter_tool(functions)

        #对问题直接进行分解的粒度不太对, 需要现在图上进行遍历发掘独立的调用链条, 再进行分解。
        #1. 先让LLM 对api的参数进行填充
        all_fill = []
        for tool in used_tools:
            api_args_fill_prompt = API_ARGS_FILL(question=new_question, api_info = tool)
            tool_res = LLM(api_args_fill_prompt, model_name)
            api_args_fill_list = strip_json_markdown(tool_res)
            if api_args_fill_list:
                continue
            all_fill.append(api_args_fill_list)
        #2. 根据填充的结果修补unkown参数
        stack = deque()
        all_nodes = {}
        for api_args_fill in all_fill:
            api_name = api_args_fill["api_name"]
            arguments = api_args_fill["arguments"]

            tool_args_info = used_tools[api_name]["docs_row"]["parameters"]["properties"]
            flag, arguments_new = remove_null_values(arguments, tool_args_info)
            # 对节点进行修改
            row_func = {"api_name": api_name, "arguments": arguments_new}
            func_node = format_api_call(row_func)
            all_nodes[func_node] = row_func
            if flag:
                stack.append(func_node)

        while stack:
            node = stack.popleft()
            #<------------------------- 先从已经构建的节点中选择 ------------------------------>
            #提取当前node的名字和unkown参数 和 unknown 参数的依赖
            api_name = node.split("(")[0]
            unknown_params = extract_unknown_fields(data = all_nodes[node]["arguments"]) # 返回列表
            dependencies, source_api_list = build_dependencies(api_link[api_name], used_tools, unknown_params)
            # 提取 all_nodes 中所有 row_func 的列表，排除当前 node
            source_nodes = [key for key, value in all_nodes.items() if value["api_name"] in source_api_list]
            source_api_names = [value["api_name"] for value in all_nodes.values() if value["api_name"] in source_api_list]

            api_desc_strings = [
                f"{api_name}: {used_tools[api_name].enhance_func_desc}" 
                for api_name in source_api_names
                if api_name in used_tools
            ]
            #提示词
            judge_link_prompt = JUDGE_LINK.format(
                question =new_question, 
                api_nodes = source_nodes,
                api_nodes_desc = api_desc_strings,
                target_api_call = all_nodes[node],
                target_api_description= {"api_name": api_name, "params_dependencies": dependencies},
            )
            judge_out = LLM(judge_link_prompt, model_name)
            judge_res = strip_json_markdown(judge_out)
            #把发现的节点和边进行保存 {'legs[0].fromId': 'Search_Flight_Location(query="Berlin")',}
            extract_call = extract_api_calls_with_path(arguments=judge_res["arguments"])
            extract_link = match_api_dependencies(extract_call, dependencies, api_name)
            Graph.extend(extract_link)

            #<-------------------- 如果判断结果仍然存在依赖没有解决, 生成新的节点---------------------->
            unknown_params2 = extract_unknown_fields(data = judge_res["arguments"]) # 返回列表
            if unknown_params2:
                dependencies2, source_api_list2 = build_dependencies(api_link[api_name], used_tools, unknown_params2)
                # 提取 all_nodes 中所有 row_func 的列表
                source_api_names2 = [value["api_name"] for value in all_nodes.values() if value["api_name"] in source_api_list2]
                api_desc_strings = [
                    used_tools[api_name].docs_row for api_name in source_api_names2 if api_name in used_tools
                ]
                # 提示词
                find_upstream_api_prompt = FIND_UPSTREAM_API.format(
                    question = new_question,
                    related_api_list = api_desc_strings,
                    target_api_call = judge_res
                )
                find_out = LLM(find_upstream_api_prompt, model_name)
                find_res = strip_json_markdown(find_out)
                #<----------- 将新的节点添加到all_nodes中------------------------------>
                for res in find_res:
                    api_name = res["api_name"]
                    unknown_params_new = extract_unknown_fields(data = res["arguments"])
                    if unknown_params_new:
                        extract_call = extract_api_calls_with_path(arguments= res["arguments"])
                        extract_link = match_api_dependencies(extract_call, dependencies2, api_name)
                        Graph.extend(extract_link)
                        continue
                    tool_args_info_new = used_tools[api_name]["docs_row"]["parameters"]["properties"]
                    flag, arguments_new = remove_null_values(res["arguments"], tool_args_info_new)
                    row_func_new = {"api_name": res["api_name"], "arguments": res["arguments"]}
                    func_node_new = format_api_call(row_func_new)
                    if func_node_new not in all_nodes:
                        all_nodes[func_node_new] = row_func
                        if flag:
                            stack.append(func_node)
                    
                    








                





            
            

            
            
        
         
        

        

        ###对问题进行分解
        # for _ in range(3):
        #     try:
        #         query_decompose_prompt = QUESATION_DECOMPOSE.format(question=new_question)
        #         query_decompose_answer = LLM(query_decompose_prompt, model_name)
        #         query_decompose_response = strip_json_markdown(query_decompose_answer)
        #         sub_questions = query_decompose_response["decomposed question"]
        #         break
        #     except:
        #         sub_questions = new_question
        # print(sub_questions)

        
        ### 记载记忆
        print("加载记忆...")
        memory = None
        print("成功加载全局记忆...")

        scratchpad = run(model_name=model_name, 
                        question=new_question, 
                        tools=tools, 
                        tool_names=tool_names, 
                        memory=memory)
        
        '''
        对答案进行后处理
        '''





    except:
        pass






if __name__ == '__main__':
    pass