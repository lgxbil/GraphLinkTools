import json
import os, sys
import glob
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from GraphLink.tool import ApiInfo
import traceback
import copy
from collections import deque
from utils_planner import extract_unknown_fields, remove_null_values, format_api_call, extract_api_calls_with_path, match_api_dependencies, build_dependencies, print_colored
from prompt1 import *
from utils.utilize import strip_json_markdown
from LLM import LLM


class APIGraphBuilder:
    def __init__(self, model_name, api_link, tools, notebooks):
        self.model_name = model_name
        self.api_link = api_link

#         tool_select = {
#     'Get_Nearby_Cities': notebooks['Get_Nearby_Cities'],
#     **{tool['name']: notebooks[tool['name']] for tool in tools if tool['name'] != 'Get_Nearby_Cities'}
# }

        tool_select = {tool['name']: notebooks[tool['name']] for tool in tools if tool['name'] in notebooks}

        self.tools = tool_select
        self.graph_edges = []
        self.all_nodes = {}

    def rewrite_question(self, query):
        for _ in range(3):
            try:
                system_prompt = QUESATION_REWRITE
                user_prompt = QUESATION_REWRITE_USER.format(question=query)
                prompt = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
                answer = LLM(prompt, self.model_name, json = 1)
                result = strip_json_markdown(answer)
                result = json.loads(result)
                return result.get("written question", query)
            except Exception as e:
                print(f"[Rewrite Error] {e}")
        return query

    def fill_api_arguments(self, question):
        filled_results = []
        for api_name , tool_info in self.tools.items():
            print(api_name)
            try:
                system_prompt = API_ARGS_FILL
                user_prompt = API_ARGS_FILL_USER.format(question=question, api_info=tool_info.docs_row)
                prompt = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
                answer = LLM(prompt, self.model_name, json = 1)
                
                fill_result = json.loads(strip_json_markdown(answer))
                print(fill_result)
                for res in fill_result:
                    if res["api_name"] == api_name:
                        filled_results.append(res)
            except Exception as e:
                print(f"[Args Fill Error] {e}")
                print("填充结果",filled_results)

        return filled_results

    def build_graph(self, filled_results, question):
        self.queue = deque()

        # 初始化节点
        for result in filled_results:
            api_name = result["api_name"]
            args = result["arguments"]

            arg_info = self.tools[api_name].docs_row["parameters"]["properties"]
            has_unknown, cleaned_args = remove_null_values(args, arg_info)

            node_key = format_api_call({"api_name": api_name, "arguments": cleaned_args})
            self.all_nodes[node_key] = {"api_name": api_name, "arguments": cleaned_args}

            if has_unknown:
                self.queue.append(node_key)

        while self.queue:
            current = self.queue.popleft()
            print_colored(f"当前节点：{current}", "red")
            self._process_node(current, question)

    def _process_node(self, node_key, question):
        api_name = node_key.split("(")[0]
        unknown_params = extract_unknown_fields(self.all_nodes[node_key]["arguments"])
        
        dependencies, source_apis = build_dependencies(self.api_link[api_name], self.tools, unknown_params)
        source_apis = list(set(source_apis))
        #source_api_list = ["api_name1", "api_name2", ...]
        #dependencies = {unknown_param1: [], "unknown_param2": []}
        #unknown_params = ['legs[0].fromId', 'legs[0].toId', 'legs[1].fromId', 'legs[1].toId']
        source_nodes = [key for key, value in self.all_nodes.items() if value["api_name"] in source_apis]

        api_descriptions = [f"{name}: {self.tools[name].enhance_func_desc}" for name in source_apis if name in self.tools]

        target_api_description = copy.deepcopy(self.tools[api_name].docs_row)
        target_api_description['depends_on'] = dependencies

        system_prompt = JUDGE_LINK
        user_prompt = JUDGE_LINK_USER.format(
            question=question,
            api_nodes=source_nodes,
            target_api_description=target_api_description,
            target_api_call= self.all_nodes[node_key],
        )
        prompt = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            answer = LLM(prompt, self.model_name, json = 1)
            judge_result = json.loads(strip_json_markdown(answer))
            print_colored(f"Judge Result: {judge_result}", "green")

            extracted_calls, _ = extract_api_calls_with_path(judge_result["arguments"])
            # print_colored(f"Extracted Calls: {extracted_calls}", "blue")
            #extracted_calls = {"参数"："api调用xx(参数1, 参数2, 参数3)", ....}
            links = match_api_dependencies(extracted_calls, self.api_link, api_name, node_key)
            self.graph_edges.extend(links)

            new_unknowns = extract_unknown_fields(judge_result["arguments"])
            if new_unknowns:
                self._find_and_add_upstream_apis(judge_result, api_name, node_key, dependencies, new_unknowns, question)

        except Exception as e:
            print(f"[Process Node Error] {e}")
            traceback.print_exc()

    def _find_and_add_upstream_apis(self, judge_result, api_name, target_node_key, dependencies, unknown_params, question,):
        dep, source_apis = build_dependencies(self.api_link[api_name], self.tools, unknown_params)
        #去重
        source_apis = list(set(source_apis))
        target_api_description = copy.deepcopy(self.tools[api_name].docs_row)
        target_api_description['depends_on'] = dep

        api_descriptions = [self.tools[name].docs_row for name in source_apis if name in self.tools]
        system_prompt = FIND_UPSTREAM_API
        user_prompt = FIND_UPSTREAM_API_USER.format(
            question=question,
            related_api_list=api_descriptions,
            target_api_call=judge_result,
            target_api_description=target_api_description,
        )
        prompt = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            answer = LLM(prompt, self.model_name, json=1)
            upstream_apis = json.loads(strip_json_markdown(answer))

            for api_data in upstream_apis:
                target_args = api_data["target_args"]
                upstream_name = api_data["source_api_name"]
                args = api_data["arguments"]

                # new_unknowns = extract_unknown_fields(args)
                # if new_unknowns:
                # extracted_calls, flag = extract_api_calls_with_path(args)
                # links = match_api_dependencies(extracted_calls, self.api_link, upstream_name)
                # self.graph_edges.extend(links)

                #可能产生幻觉 先过滤掉
                if upstream_name not in self.tools: continue
                if target_args not in unknown_params: continue

                arg_info = self.tools[upstream_name].docs_row["parameters"]["properties"]
                has_unknown, cleaned_args = remove_null_values(args, arg_info)
                node_key = format_api_call({"api_name": upstream_name, "arguments": cleaned_args})

                extracted_calls = {
                    target_args: node_key
                }
                print_colored(f"Extracted Calls: {extracted_calls}", "blue")
                links = match_api_dependencies(extracted_calls, self.api_link, api_name, target_node_key)
                self.graph_edges.extend(links)

                if node_key not in self.all_nodes:
                    self.all_nodes[node_key] = {"api_name": upstream_name, "arguments": cleaned_args}
                    if has_unknown:
                        self.queue.append(node_key)

        except Exception as e:
            print(f"[Find Upstream API Error] {e}")
            traceback.print_exc()
    # def check_nodeandedge(self,):
    #     api_nodes = [value for key, value in self.all_nodes.items()]
    #     edges = self.clean_edges()
    #     for edge in edges:
    #         to_api = edge['to_api']
    #         target_param = edge['target_param']
    #         for api_node in api_nodes:
    #             if api_node['api_name'] == to_api:
    #                 unknown_params = extract_unknown_fields(api_node["arguments"])
                    

    def question_to_graph(self, question):
        api_nodes = [key for key, value in self.all_nodes.items()]
        edges = self.clean_edges()
        # api_descriptions = [self.tools[name].docs_row for name in api_nodes]
        system_prompt = QUESATION_DECOMPOSE1
        user_prompt = QUESATION_DECOMPOSE_USER1.format(
            question = question,
            nodes = api_nodes,
            edges = edges,
        )
        prompt = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        answer = LLM(prompt, self.model_name, json=1)
        sub_tasks = json.loads(strip_json_markdown(answer))
        return sub_tasks
    
    def process_tasks(self, sub_tasks, fc_chain):
        tools = []
        # seen_api_names = set()  # 用于去重
        
        # for key, value in sub_tasks.items():
        #     for node in value["Nodes"]:
        #         api_name = node.split("(")[0]
        #         if api_name not in self.tools:
        #             continue
        #         if api_name in seen_api_names:
        #             continue  # 去重：如果已经加过就跳过

        #         seen_api_names.add(api_name)  # 标记已经处理过

        #         row_docs = self.tools[api_name].docs_row
        #         row_docs["response_schema"] = self.tools[api_name].api_response_schema
        #         tools.append(row_docs)
        for api_name in fc_chain:
            row_docs = self.tools[api_name].docs_row
            row_docs["response_schema"] = self.tools[api_name].api_response_schema
            tools.append(row_docs)
        
        return tools


    def clean_edges(self,):
        unique_edges_set = set()
        unique_edges = []

        for edge in self.graph_edges:
            key = (edge["from_api"], edge["response_path"], edge["target_param"], edge["to_api"])
            if key not in unique_edges_set:
                unique_edges_set.add(key)
                unique_edges.append(edge)
        return unique_edges
    
def run_single(data, model_name, api_link, notebooks):
    try:
        conversations = data["conversations"]
        functions = data["functions"]
        def normalize_fc_name(name):
            if name == 'Get_Hotel_Reviews(Tips)_Sort_Option':
                return 'Get_Hotel_Reviews_Sort_Option'
            if name == 'Get_Hotel_Reviews(Tips)':
                return 'Get_Hotel_Reviews'
            return name  # 默认不变
        for fc in functions:
            fc['name'] = normalize_fc_name(fc['name'])
        
        for turn in conversations:
            if "function_call" in turn:
                for fc in turn['function_call']:
                    fc['name'] = normalize_fc_name(fc['name'])

        fc_chain = set()
        for turn in conversations:
            if "function_call" in turn:
                for fc in turn['function_call']:
                    fc_chain.add(fc['name'])
        fc_chain = list(fc_chain)
        

        original_query = conversations[0]["content"]

        builder = APIGraphBuilder(model_name, api_link, functions, notebooks)

        print("[Step] Rewriting question...")
        new_question = builder.rewrite_question(original_query)
        print_colored(f"Rewritten Question: {new_question}", "green")

        # exit()
        print("[Step] Filling API arguments...")
        filled_results = builder.fill_api_arguments(new_question)
        print_colored(f"Filled Results: {json.dumps(filled_results, indent=4, ensure_ascii=False)}", "green")



        print("[Step] Building dependency graph...")
        builder.build_graph(filled_results, new_question)
        print_colored({json.dumps(builder.graph_edges, indent=4, ensure_ascii=False)}, "green")
        print_colored({json.dumps(builder.all_nodes, indent=4, ensure_ascii=False)}, "green")
        

        # exit()
        #根据流程图对用户问题进行分解
        print("[Step] Decomposing question into sub-tasks...")
        sub_tasks = builder.question_to_graph(new_question)
        print_colored({json.dumps(sub_tasks, indent=4, ensure_ascii=False)}, "green")
         
        #对分解的子任务中的tools
        tools = builder.process_tasks(sub_tasks, fc_chain)
        sub_tasks["question"] = new_question
        
        return sub_tasks, tools

    except Exception as e:
        print(f"[Error] {e}")
        traceback.print_exc()


if __name__ == "__main__":
    #  def __init__(self, model_name, api_link, tools):
    model_name = "qwen2.5-7b-instruct"
    api_link_floder = "/home/snrobot/lin/GraphLinkTools/gound_truth/api_link_gt_clean(3).jsonl"
    api_link = json.load(open(api_link_floder, 'r'))

    api_folder_path = "/home/snrobot/lin/GraphLinkTools/GraphPlanner/data/APIinfo_update(2)"
    info_files = glob.glob(os.path.join(api_folder_path, '*.json'))
    notebooks = {}
    for i, file_path in enumerate(info_files):
        notebook = ApiInfo(**json.load(open(file_path)))
        notebooks[notebook.name] = notebook

    # apigraph_builder = APIGraphBuilder(model_name, api_link, tools)
    data = "/home/snrobot/lin/GraphLinkTools/GraphPlanner/ComplexFuncBench/data/ComplexFuncBench.jsonl"
    
    with open(data, 'r') as f:
        for i, line in enumerate(f):
            if i != 0: continue
            data = json.loads(line)
            sub_tasks, tools = run_single(data, model_name, api_link, notebooks)
            print(sub_tasks)
            # output_dir = "/home/snrobot/lin/GraphLinkTools/GraphPlanner/tmp"
            # os.makedirs(output_dir, exist_ok=True)

            # # 文件路径
            # output_file = os.path.join(output_dir, f"output_results_{i}.json")
            # output_data = {
            #     "sub_tasks": sub_tasks,
            #     "tools": tools
            # }
            # with open(output_file, "w", encoding="utf-8") as out_f:
            #     json.dump(output_data, out_f, indent=4, ensure_ascii=False)
            
