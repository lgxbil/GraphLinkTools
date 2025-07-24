import re
import copy
import json
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
from ComplexFuncBench.mock_function.base_runner import ModelRunner


class QwenRunner(ModelRunner):
    def __init__(self, args, logger, data):
        super().__init__(args, logger)
        self.model_name = args.model_name
        self.init_gloden_result(data)
    
    def get_standard_functions(self, functions):
        return [{"type": "function", "function": copy.deepcopy(func)} for func in functions]
    
    def init_gloden_result(self, data):
        #data是单条数据样本
        convs, self.functions = data['conversations'], data['functions']
        self.CompareClass.add_free_function(convs)
        self.init_golden(convs)
    
    def get_mock_res(self, pred_calls):
        function_calls = [pred_calls]
        # error_message = [{"error_type": "param_missing", "content": f"Missing parameter {k} in prediction."}]
        self.error_message, success_map, success_matched, format_error, success_matched_func = self.CompareClass.compare_turn_prediction(
            self.functions, [], 
            copy.deepcopy(function_calls), self.golden_fcs, 
            self.golden_obs
        )
        # 错误信息 格式[{"error_type": "value_error", "content": f"Parameter {k} value do not equal to golden."}]
        if len(success_map) == 0 and format_error == {}:
            #return messages, error_info, success_turn, self.correct_count
            # return self.return_result([], self.error_message)
            error = {"status": False, "message":self.error_message[0], "data":None}
            return error
        ################## 统计信息 ##################
        self.correct_count += len(success_map)
        for key in success_matched_func:
            # 如果 key 已经在 correct_count_dict 中，增加计数
            if key in self.correct_count_dict:
                self.correct_count_dict[key] += 1
            else:
                # 如果 key 不在 correct_count_dict 中，初始化计数为 1
                self.correct_count_dict[key] = 1

        real_time_obs = []
        for t, function_call in enumerate(function_calls):
            if t in success_map:
                #{"status": true, "message": "Success", "data": ...}
                temp_obs = success_map[t]
                
            elif t in format_error:
                #原{"error": f"Parameter {param_name} of function {used_func['name']} should be an array, but {type(param_value)} is provided."}
                #封装一下呢
                temp_obs = {"status": False, "message": format_error[t], "data": None}
                # temp_obs = format_error[t]
            else:
                #{"api_status": True, "content": "There is a problem with your api call, please double-check for possible problems."}
                temp_obs = self.unexpect_call_resp
                
            real_time_obs.append(temp_obs)
        #success_matched.append(match_item['golden_call'])
        self.process_matches(success_matched)

        return real_time_obs[0]
        

    def run(self, data):
        convs, functions = data['conversations'], data['functions']
        self.CompareClass.add_free_function(convs)
        standard_functions = self.get_standard_functions(functions)

        messages = []
        query = convs[0]['content']
        messages.append({"role": "user", "content": query})

        self.init_golden(convs)

        while True:
            llm_response = self.model(messages, tools=standard_functions)

            if llm_response is None:
                raise NotImplementedError("LLM response is None")

            if llm_response['tool_calls'] != None:
                if self.golden_fcs == []:
                    self.logger.error(f"Output FC:\n{llm_response}")
                    return self.return_result(messages, {"error_type": "func_hallucination", "content": "`self.golden_fcs == []`. Expected to stop. But Model continue to output function call."})
                if llm_response['content'] is None:
                    llm_response['content'] = ""
                self.model.messages.append(llm_response)
                tool_calls = llm_response['tool_calls']

                function_calls = []
                for tool_call in tool_calls:
                    function_call = self.get_standard_fc(tool_call)
                    if function_call is None:
                        return self.return_result(messages, {"error_type": "decode_error", "content": f"{tool_call} is not Valid."})
                    function_calls.append(function_call)
                self.logger.info(f"Function Calls: \n{json.dumps(function_calls, ensure_ascii=False, indent=4)}\n")
                self.logger.info(f"Golden Function Call: \n{json.dumps(self.golden_fcs, ensure_ascii=False, indent=4)}\n")
                messages.append({"role": "assistant", "function_call": function_calls})
                
                self.error_message, success_map, success_matched, format_error = self.CompareClass.compare_turn_prediction(
                    functions, messages[:-1], 
                    copy.deepcopy(function_calls), self.golden_fcs, 
                    self.golden_obs
                )
                if len(success_map) == 0 and format_error == {}:
                    return self.return_result(messages, self.error_message)
                self.correct_count += len(success_map)

                real_time_obs = []
                for t, function_call in enumerate(function_calls):
                    if t in success_map:
                        temp_obs = success_map[t]
                    elif t in format_error:
                        temp_obs = format_error[t]
                    else:
                        temp_obs = self.unexpect_call_resp
                        
                    real_time_obs.append(temp_obs)
                    self.model.messages.append(
                        {
                            "name": function_call['name'],
                            "role": "tool",
                            "content": json.dumps(temp_obs, ensure_ascii=False)
                        }
                    )
                self.process_matches(success_matched)
                    
                self.logger.info(f"Observations:\n{json.dumps(real_time_obs, ensure_ascii=False, indent=4)}\n")
                messages.append({"role": "observation", "content": real_time_obs})

            elif llm_response['tool_calls'] == None:
                final_response = llm_response['content']
                self.logger.info(f"Final Response: {final_response}\n")
                messages.append({"role": "assistant", "content": final_response})

                return self.return_result(messages)

            else:
                return self.return_result(messages, {"error_type": "unknown_error", "content": "llm_response is None"})