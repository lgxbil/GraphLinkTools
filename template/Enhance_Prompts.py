from dataclasses import dataclass
import json

@dataclass
class EnchancePrompts:
    def Enchance_API_Desc(self, api_info, api_summary, Example):
        summary = Example.get("response_summary")
        api = Example.get("api")
        dunc_desc = Example.get("func_description")
        system = f"""
You will receive an API document containing:
- The name of the API,
- A functional description of the API (which may be empty or incomplete),
- The API parameters,
- The API Response Summary(which may be empty).
Your task is to enhance the functional description of the API in the documentation. This enhancement should help users better understand the functionality of the API and align its semantics with potential user queries.

#RULES:
1. **Application Scenarios**: Describe the primary use cases or applicable scenarios for the API.
2. **Core Functionality**: Explain the key features and search targets.
3. **Expected Output**: Specify the detailed information included in the API response. 
4. Describe in the order of the first 3 rules, no more than 80 words.

By following these rules, you will create a functional description that is not only informative but also user-friendly and aligned with real-world user needs.
Pay attention to the function description, try not to exceed 80 words.

#EXAMPLES:
API Response Summary:
{summary}
API Row Response:
{json.dumps(api, indent=4, ensure_ascii=False)}
Enchance Function Description:
{dunc_desc}

# OUTPUT:
Enchance Function Description: << ENHANCE FUNCTION DESCRIPTION >>
"""
        user = f"""
API Response Summary:
{api_summary}
API Row Response:
{json.dumps(api_info, indent=4, ensure_ascii=False)}
Enchance Function Description:
"""
        messages = [
            {"role": "system","content": system},
            {"role": "user","content":  user},
        ]
        
        return messages


    def Enchance_API_Params(self, tool_docs, Example):
        system = f"""
You will receive an API document containing:
- The name of the API,
- A functional description of the API (which may be empty or incomplete),
- The API parameters,
- The API response(which may be empty).

#GOLD:

#RULES:
1. 

By following these rules, you will enhance parameter descriptions that are informative, user-friendly, and aligned with real-world user needs. Pay attention to each parameter description, and try not to exceed 30 words.

#EXAMPLES:
{Example}

# EXAMPLE JSON OUTPUT:
{{
    "enhanced_parameters": {{
        parameter_name1: "enhanced description",
        parameter_name2: "enhanced description",
        ....
        parameter_nameN: "enhanced description"
    }}
}}
"""
        return system
    
    def Enchance_API_Response(self, Example, api_response, api_summary):
        response = Example.get("response")
        summary = Example.get("response_summary")
        response_fields = Example.get("response_fields")
        system = f"""
You are an API response field parser. You will receive an API response in JSON format along with its easy-to-read natural language form. Your task is to generate the type, description, for each response field.

#RULES:
1. Infer the meaning and purpose of each field based on its values: The API response has been shortened, and there are up to three different values for each field to help you infer its meaning and purpose.
2. Determine the correct data type for each field (e.g., String, Number, Boolean, Object, Array, Date, etc.). If a field contains nested objects or lists, clearly indicate the structure.
3. Field descriptions should reflect the characteristics of the API response as much as possible.Please describe the response fields in as much detail as possible.

#EXAMPLES:
API Response Summary:
{summary}
API Row Response:
{json.dumps(response, indent=4, ensure_ascii=False)}
API Response Field Description:
{json.dumps(response_fields, indent=4, ensure_ascii=False)}

#OUTPUT FORMAT:
Output in hierarchical JSON format.
"""
        user = f"""
API Response Summary:
{api_summary}
API Row Response:
{json.dumps(api_response, indent=4, ensure_ascii=False)}
API Response Field Description:
"""
        messages = [
            {"role": "system","content": system},
            {"role": "user","content":  user},
        ]
        
        return messages
    def Summary_Response(self, api_resopnse, example:dict):
        resopnse = example.get("response")
        summary = resopnse.get("response_summary")
        
        system = f"""
You are an API response summarizer. You will receive an API response, which is often in the form of a dictionary or list and can be difficult for users to understand. Your task is to convert the response into easy-to-read information using natural language.

#Example:
API Response:
{json.dumps(resopnse, indent=4, ensure_ascii=False)}
API Response Summary:
{summary}
"""
        user = f"""
API Response:
{api_resopnse}
API Response Summary:
"""
        messages = [
            {"role": "system","content": system},
            {"role": "user","content":  user},
        ]
        
        return messages


if __name__ == '__main__':
    c = EnchancePrompts()
    print(c.Enchance_API_Params())