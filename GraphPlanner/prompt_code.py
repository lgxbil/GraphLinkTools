
class CodePrompt:

    
    def subtask_summary(self, query, context):
        subtask_summary_example = """
(Begin of Example 1)

Query: Search for the fastest flight from Edinburgh to Lisbon on 2024-11-20. Obtain the flight arrival time, and provide data for the subsequent decision on whether the Edinburgh Castle tour can be joined on the same day.

Ipython Shell Context:
In [1]:
[code]
Out [1]:
The fastest flight from Edinburgh to Lisbon on 2024-11-20, lands at 2024-11-20T17:10.

Output:
[Yes] According to the code and execution results, the arrival time of the fastest flight from Edinburgh to Lisbon on 2024-11-20 has been successfully retrieved as 17:10. This time can be used for comparison in subsequent subtasks.

(End of Example 1)

(Begin of Example 2)

Query: 
Retrieve the destination ID for Canberra and the categories filter for family rooms that allow pets. This subtask involves calling Search_Hotel_Destination to get the dest_id for Canberra and then using Get_Filter to retrieve the appropriate categories_filter.

Ipython Shell Context:
In [1]:
filter_result = F.Get_Filter(get_filter_params)
if filter_result.get('status'):
    raise Exception(f"Get_Filter failed: {filter_result.get('messages', 'Unknown error')}")
# Extract categories_filter for family rooms and pet-friendly rooms
categories_filter = next(
    (option['genericId'] for filter in filter_result['filters'] for option in filter['options'] if 'Family' in option['title'] and 'Pet' in option['title']),
    None
)
print(f"Categories Filter: {categories_filter}")

Out [1]:
Family and Pet Categories Filter: None

Output:
[No] Although the code has been continuously revised to fix execution errors, the execution result is still empty. The code execution result did not return a genericId that satisfies both conditions: filtering for family rooms and allowing pets. It may be necessary to review the filter_result output using an LLM to extract and filter the relevant information.

(Begin of Example 1)
"""
        system = f"""
You are a code execution analyzer. The code involves a series of API calls to solve a user's problem and is executed interactively through an IPython shell. You need to determine whether the execution results meet the user's requirements, provide a summary, and analyze which requirements have not been fulfilled.

Examples:
{subtask_summary_example}

Output Format:
[Yes/No] (Your Reason)

    
        """
        user = f"""
Query: 
{query}
Ipython Shell Context:
{context}
Output:
"""
        
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]

        return messages
    def select_variable(self, query, shell_context, error_info, valid_variables_name):
        
        select_example = """
Query: 
Retrieve the destination ID for Canberra and the categories filter for family rooms that allow pets. This subtask involves calling Search_Hotel_Destination to get the dest_id for Canberra and then using Get_Filter to retrieve the appropriate categories_filter.

Ipython Shell Context:
In [1]:
filter_result = F.Get_Filter(get_filter_params)
if filter_result.get('status'):
    raise Exception(f"Get_Filter failed: {filter_result.get('messages', 'Unknown error')}")
# Extract categories_filter for family rooms and pet-friendly rooms
categories_filter = next(
    (option['genericId'] for filter in filter_result['filters'] for option in filter['options'] if 'Family' in option['title'] and 'Pet' in option['title']),
    None
)
print(f"Categories Filter: {categories_filter}")

Out [1]:
Family and Pet Categories Filter: None

Error Analysis:
[No] Although the code has been continuously revised to fix execution errors, the execution result is still empty. The code execution result did not return a genericId that satisfies both conditions: filtering for family rooms and allowing pets. It may be necessary to review the filter_result output using an LLM to extract and filter the relevant information.

valid_variables_name:
[filter_result, categories_filter, get_filter_params]

Output:
[filter_result]
"""
        system_prompt = f"""
You will receive a complex user problem that requires calling multiple APIs to solve, along with the context of interactive programming based on IPython Shell. Currently, there are issues that cannot be resolved through further coding alone, and it is necessary to examine the specific API call results for further investigation. Please select the stored variables that are helpful for solving the current problem.

#Example:
{select_example}

#Output Format:
Please output in the following JSON format that can be parsed by Python's json.loads function.
[Your Selected valid variables name]

#Note:
The selected variables can only be chosen from the provided "valid_variables_name" list and must not be fabricated. It is also acceptable to select none of them.
"""
        user_prompt = f"""
Query: 
{query}
Ipython Shell Context:
{shell_context}
Error Analysis:
{error_info}
valid_variables_name:
{valid_variables_name}
Output:
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        return messages
    def anaylsis_result(self, query, shell_context, valid_result):
        
        anaylysis_example = """
Query: 
Retrieve the destination ID for Canberra and the categories filter for family rooms that allow pets. This subtask involves calling Search_Hotel_Destination to get the dest_id for Canberra and then using Get_Filter to retrieve the appropriate categories_filter.

Ipython Shell Context:
In [1]:
filter_result = F.Get_Filter(get_filter_params)

# Extract categories_filter for family rooms and pet-friendly rooms
categories_filter = next(
    (option['genericId'] for filter in filter_result['filters'] for option in filter['options'] if 'Family' in option['title'] and 'Pet' in option['title']),
    None
)
print(f"Categories Filter: {categories_filter}")

Out [1]:
Family and Pet Categories Filter: None

Error Analysis:
[No] Although the code has been continuously revised to fix execution errors, the execution result is still empty. The code execution result did not return a genericId that satisfies both conditions: filtering for family rooms and allowing pets. It may be necessary to review the filter_result output using an LLM to extract and filter the relevant information.

valid_result:
"options": [
    {
        title:"Family rooms"
        genericId:"facility::28"
        countNotAutoextended:475
    },
    {
        title:"Pets allowed"
        genericId:"facility::4"
        countNotAutoextended:9
    }
]
Output:
According to the result of calling Get_Filter, the filter_result shows that the two filter IDs suitable for family rooms and allowing pets are "facility::28,facility::4"
"""
        system_prompt = f"""
You are an API response analysis expert, responsible for identifying key information from API responses that can help solve complex user problems. You will receive a user problem that requires calling multiple APIs to resolve, along with an interactive programming context based on IPython Shell and the related coding issues. Your task is to extract information from the existing API responses that is helpful for addressing the current coding problem.

#Example:
{anaylysis_example}

#Output:
[your output here]
Notes:Directly analyze the response to extract information that is useful for solving the problem. Do not provide any code. Do not provide any code. Do not provide any code.
"""
        user_prompt = f"""
Query: 
{query}
Ipython Shell Context:
{shell_context}
valid_result:
{valid_result}
Output:
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        return messages


