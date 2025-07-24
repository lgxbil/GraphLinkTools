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

        tool_select = {
    'Get_Nearby_Cities': notebooks['Get_Nearby_Cities'],
    **{tool['name']: notebooks[tool['name']] for tool in tools if tool['name'] != 'Get_Nearby_Cities'}
}

        # tool_select = {tool['name']: notebooks[tool['name']] for tool in tools}

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
                answer = LLM(prompt, self.model_name)
                result = strip_json_markdown(answer)
                result = json.loads(result)
                return result.get("written question", query)
            except Exception as e:
                print(f"[Rewrite Error] {e}")
        return query

    def fill_api_arguments(self, question):
        filled_results = []
        for api_name , tool_info in self.tools.items():
            try:
                system_prompt = API_ARGS_FILL
                user_prompt = API_ARGS_FILL_USER.format(question=question, api_info=tool_info.docs_row)
                prompt = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
                answer = LLM(prompt, self.model_name)
                
                fill_result = json.loads(strip_json_markdown(answer))
                # print(fill_result)
                for res in fill_result:
                    # print(res)
                    if res["api_name"] == api_name:
                        filled_results.append(res)
            except Exception as e:
                print(f"[Args Fill Error] {e}")

        return filled_results

    def build_graph(self, filled_results, question):
        queue = deque()

        # 初始化节点
        for result in filled_results:
            api_name = result["api_name"]
            args = result["arguments"]

            arg_info = self.tools[api_name].docs_row["parameters"]["properties"]
            has_unknown, cleaned_args = remove_null_values(args, arg_info)

            node_key = format_api_call({"api_name": api_name, "arguments": cleaned_args})
            self.all_nodes[node_key] = {"api_name": api_name, "arguments": cleaned_args}

            if has_unknown:
                queue.append(node_key)

        while queue:
            current = queue.popleft()
            print_colored(f"当前节点：{current}", "red")
            self._process_node(current, question, queue)

    def _process_node(self, node_key, question, queue):
        api_name = node_key.split("(")[0]
        unknown_params = extract_unknown_fields(self.all_nodes[node_key]["arguments"])

        dependencies, source_apis = build_dependencies(self.api_link[api_name], self.tools, unknown_params)
#source_api_list = ["api_name1", "api_name2", ...] # 依赖的api列表是从self.tools 中选的
#dependencies = {unknown_param1: [{'source_api': 'Search_Flight_Location', 'res_path': '$[0].id'}], "unknown_param2": []}
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
            answer = LLM(prompt, self.model_name)
            judge_result = json.loads(strip_json_markdown(answer))
            print_colored(f"Judge Result: {judge_result}", "green")

            extracted_calls, _ = extract_api_calls_with_path(judge_result["arguments"])
            # print_colored(f"Extracted Calls: {extracted_calls}", "blue")
            #extracted_calls = {"参数"："api调用xx(参数1, 参数2, 参数3)", ....}
            links = match_api_dependencies(extracted_calls, self.api_link, api_name, node_key)
            self.graph_edges.extend(links)

            new_unknowns = extract_unknown_fields(judge_result["arguments"])
            if new_unknowns:
                self._find_and_add_upstream_apis(judge_result, api_name, node_key, dependencies, new_unknowns, question, queue)

        except Exception as e:
            print(f"[Process Node Error] {e}")
            traceback.print_exc()

    def _find_and_add_upstream_apis(self, judge_result, api_name, target_node_key, dependencies, unknown_params, question, queue):
        dep, source_apis = build_dependencies(self.api_link[api_name], self.tools, unknown_params)
        #去重
        source_apis = list(set(source_apis))

        api_descriptions = [self.tools[name].docs_row for name in source_apis if name in self.tools]
        system_prompt = FIND_UPSTREAM_API
        user_prompt = FIND_UPSTREAM_API_USER.format(
            question=question,
            related_api_list=api_descriptions,
            target_api_call=judge_result,
        )
        prompt = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            answer = LLM(prompt, self.model_name)
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
                        queue.append(node_key)

        except Exception as e:
            print(f"[Find Upstream API Error] {e}")
            traceback.print_exc()
    def question_to_graph(self, question):
        api_nodes = [value["api_name"] for key, value in self.all_nodes.items()]
        api_descriptions = [self.tools[name].docs_row for name in api_nodes]
        system_prompt = QUESATION_DECOMPOSE
        user_prompt = QUESATION_DECOMPOSE_USER.format(
            question = question,
            call_flow_edges = self.graph_edges,
            related_api_information = "",
        )
        prompt = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        answer = LLM(prompt, self.model_name)
        sub_tasks = json.loads(strip_json_markdown(answer))
        return sub_tasks

def run_single(data, model_name, api_link, notebooks):
    try:
        conversations = data["conversations"]
        functions = data["functions"]

        original_query = conversations[0]["content"]

        builder = APIGraphBuilder(model_name, api_link, functions, notebooks)

        # print("[Step] Rewriting question...")
        # new_question = builder.rewrite_question(original_query)
        # print_colored(f"Rewritten Question: {new_question}", "green")

        # print("[Step] Filling API arguments...")
        # filled_results = builder.fill_api_arguments(new_question)
        # print_colored(f"Filled Results: {json.dumps(filled_results, indent=4, ensure_ascii=False)}", "green")

        # exit()
        new_question = "Please book the cheapest flight from Beijing to London for 2024-12-05. Additionally, arrange a taxi to pick me up two hours after the landing time and take me to the British Museum." 
        filled_results =  [
             {
        "api_name": "Search_Flights",
        "arguments": {
            "fromId": "unknown(Beijing airport ID needs to be retrieved from another API)",
            "toId": "unknown(London airport ID needs to be retrieved from another API)",
            "departDate": "2024-12-05",
            
        }
    },
            {
        "api_name": "Taxi_Search_Location",
        "arguments": {
            "query": "British Museum",
            "languagecode": None
        }
    },
            {
        "api_name": "Search_Taxi",
        "arguments": {
            "pick_up_place_id": "",
            "drop_off_place_id": "unknown(need to retrieve the British Museum's place ID )",
            "pick_up_date": "unknown(need to retrieve the landing date)",
            "pick_up_time": "unknown(need to calculate the pick-up time by adding two hours to the landing time)",
        }
    },
    
    
]
        print("[Step] Building dependency graph...")
        builder.build_graph(filled_results, new_question)
        print_colored({json.dumps(builder.graph_edges, indent=4, ensure_ascii=False)}, "green")
        print_colored({json.dumps(builder.all_nodes, indent=4, ensure_ascii=False)}, "green")
        exit()
        #根据流程图对用户问题进行分解
        print("[Step] Decomposing question into sub-tasks...")
        sub_tasks = builder.question_to_graph(new_question)
        # print_colored(sub_tasks, color='red')


        # print("[Done] Graph edges:")
        # for edge in builder.graph_edges:
        #     print(edge)
        
            
        return builder.graph_edges, sub_tasks

    except Exception as e:
        print(f"[Error] {e}")
        traceback.print_exc()


if __name__ == "__main__":
    #  def __init__(self, model_name, api_link, tools):
    model_name = "qwen2.5-72b-instruct"
    api_link_floder = "/home/snrobot/lin/GraphLinkTools/gound_truth/api_link_gt_clean(2).jsonl"
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
            if i != 550: continue
            data = json.loads(line)
            graph_edges, sub_tasks = run_single(data, model_name, api_link, notebooks)
            print(f"Graph Edges: {graph_edges}")
            print(f"Sub Tasks: {sub_tasks}")
            break
