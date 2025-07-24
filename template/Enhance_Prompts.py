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
2. **Core Functionality**: Explain the key features and search targets, Pay attention to the relationship between input parameters and the response.
3. **Expected Output**: Specify the detailed information included in the API response.
4. Describe in the order of the first 3 rules, no more than 60 words.

By following these rules, you will create a functional description that is not only informative but also user-friendly and aligned with real-world user needs.
Do not assume that the API can only return the specific term just because it appears in the response
Pay attention to the function description, try not to exceed 60 words.

#EXAMPLES:
API Response Summary:
{summary}
API Row Information:
{json.dumps(api, indent=4, ensure_ascii=False)}
Enchance Function Description:
{dunc_desc}

# OUTPUT:
Enchance Function Description: << ENHANCE FUNCTION DESCRIPTION >>
"""
        user = f"""
API Response Summary:
{api_summary}
API Row Information:
{json.dumps(api_info, indent=4, ensure_ascii=False)}
Enchance Function Description:
"""
        messages = [
            {"role": "system","content": system},
            {"role": "user","content":  user},
        ]
        
        return messages


    def Enchance_API_Params(self, response_summary, api_info, Example):
        summary = Example.get("response_summary")
        api = Example.get("api")
        params = Example.get("api_params")
        system = f"""
You will receive an API document containing:
- The name of the API,
- A functional description of the API (which may be empty or incomplete),
- The API parameters,
- API Response Summary(which may be empty).

#GOLD:
Your task is to fix the inaccurate and incomplete descriptions of API parameter fields based on the API's response and the API itself.

#RULES:
1. Focus on interpreting parameter definitions. If example values are provided, deduce the parameter's purpose based on those examples.
2. Please describe the parameter fields in as much detail as possible but don't exceed 30 wrods.

#EXAMPLES:
API Response Summary:
{summary}
API Info:
{json.dumps(api, indent=4, ensure_ascii=False)}
Enchance parameter Description:
{json.dumps(params, indent=4, ensure_ascii=False)}

# JSON OUTPUT FORMAT:
{{
    "enhanced_parameters": {{
        parameter_name1: "enhanced description",
        parameter_name2: "enhanced description",
        ....
        parameter_nameN: "enhanced description"
    }}
}}
"""
        user = f"""
API Response Summary:
{response_summary}
API Info:
{json.dumps(api_info, indent=4, ensure_ascii=False)}
Enchance parameter Description:   
"""
        messages = [
            {"role": "system","content": system},
            {"role": "user","content":  user},
        ]
        return messages
    
    def Enchance_API_Response(self, Example, api_response, api_summary):
        system = f"""
You are an API response field parser. You will receive an API response in JSON format along with its easy-to-read natural language form. Your task is to generate the type, description, for each response field.Do not add any fields other than the type and description fields.

#NOTES:
1. Infer the meaning and purpose of each field based on its values: The API response has been shortened, and there are up to three different values for each field to help you infer its meaning and purpose.
2. Determine the correct data type for each field (e.g., String, Number, Boolean, Object, Array, Date, etc.). If a field contains nested objects or lists, clearly indicate the structure.
3. Field descriptions should reflect the characteristics of the API response as much as possible.Please describe the response fields in as much detail as possible.
4. You may receive fragments of the response

#EXAMPLES1:
API Row Response:
[
    {{
        "name": "Property currency",
        "code": "hotel_currency",
        "encodedSymbol": "&#x20AC;&#163;US$",
        "symbol": "\u20ac$\u00a3"
    }},
    {{
        "name": "Argentine Peso",
        "code": "ARS",
        "encodedSymbol": "AR$",
        "symbol": "AR$"
    }},
    {{
        "name": "Australian Dollar",
        "code": "AUD",
        "encodedSymbol": "AUD",
        "symbol": "AUD"
    }}
]
API Response Field Description:
{{
    "response_fields":[
        "name": {{
            "type": "String",
            "description": "The display name of the currency (e.g., 'Property currency')."
        }},
        "code": {{
            "type": "String",
            "description": "The currency code (e.g., 'hotel_currency')."
        }},
        "encodedSymbol": {{
            "type": "String",
            "description": "The encoded symbol representation of the currency (e.g. 'AUD')."
        }},
        "symbol": {{
            "type": "String",
            "description": "The standard symbol representation of the currency (e.g.'AUD')."
        }}
    ]
}}

#EXAMPLES2:
API Row Response:
{{
    "base_currency": "USD",
    "base_currency_date": "2025-05-18",
    "exchange_rates": [
        {{
            "currency": "ATS",
            "exchange_rate_buy": "12.33502980"
        }},
        {{
            "currency": "ROL",
            "exchange_rate_buy": "44333.27448071"
        }},
        {{
            "currency": "MVR",
            "exchange_rate_buy": "15.41000003"
        }}
    ]
}}
API Response Field Description:
{{
    "response_fields": {{
        "base_currency": {{
            "type": "String",
            "description": "The base currency code (ISO 4217) against which exchange rates are provided. In this case, it is USD (US Dollar)."
        }},
        "base_currency_date": {{
            "type": "Date",
            "description": "The date for which the exchange rates are provided, formatted as YYYY-MM-DD."
        }},
        "exchange_rates": {{
            "type": "Array",
            "description": "A list of exchange rates for various currencies against the base currency (USD).",
            "ar_items": {{
                "type": "Object",
                "description": "An object representing the exchange rate details for a specific currency.",
                "ob_properties": {{
                    "currency": {{
                        "type": "String",
                        "description": "The target currency code (ISO 4217) for which the exchange rate is provided (e.g., ATS, ROL, MVR)."
                    }},
                    "exchange_rate_buy": {{
                        "type": "String",
                        "description": "The buying exchange rate from the base currency (USD) to the target currency. Represented as a string to preserve precision."
                    }}
                }}
            }}
        }}
    }}
}}


#Output Hierarchical Nested JSON format Format:

Note that 'ob_properties' and 'ar_items' are used to represent the nesting of dictionaries and lists, respectively.Ensure that each Object and Array has a summary description.Do not generate extra fields.MMaintain the nested format of the API Row Response.
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
        summary = example.get("response_summary")
        
        system = f"""
You are an API response summarizer. You will receive an API response, which is often in the form of a dictionary or list and can be difficult for users to understand. Your task is to convert the response into easy-to-read information using natural language.Don't answer in points, use fluent language to form a summary of the response

#Example:
API Response:
{json.dumps(resopnse, indent=4, ensure_ascii=False)}
API Response Summary:
{summary}
"""
        user = f"""
API Response:
{json.dumps(api_resopnse["observation"], indent=4, ensure_ascii=False)}
API Response Summary:
"""
        messages = [
            {"role": "system","content": system},
            {"role": "user","content":  user},
        ]
        
        return messages


if __name__ == '__main__':
    c = '''
    {{
    "response_fields":{{
        "fieldName1": {{
            "type": "Object",
            "description": "Summary description of the dictionary object",
            "ob_properties": {{
            //Nested fields (for objects)
            ...
            "fieldName4": {{
                    "type": "Array",
                    "description": "Summary description of the Array object",
                    "ar_items": {{
                    // For arrays, the type of items inside
                    }}
                }}
            }},
            ...
            "fieldNameN": {{
                    "type": "DataType",
                    "description": "Human-readable description",
            }}
        }}
    }}
}}
    '''
    c = EnchancePrompts()
    print(c.Enchance_API_Params())