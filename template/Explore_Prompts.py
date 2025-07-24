from dataclasses import dataclass

@dataclass
class ExplorePrompts:
    
    def explore_api_by_required(self, tool_docs, Example):
        system = f"""
Your task is to answer the user's query as best you can. You have access to the tools, which you can use via API call to help with your response：

# GOALS:
It is June 5th, 2025, and many real-time APIs are unable to query historical information.Now you have the chance to explore the available APIs. You can do this by 1) synthesizing some natural user query that calling the API could help, 2) extracting the parameters needed to call these APIs from the generated query, and 3) Here, you can focus on queries that only require calling the API once.

# NOTES:
1. Now, first input your synthesized user query. You should make the query natural - for example, try to avoid using the provided API descriptions or API names in the query, as the user does not know what APIs you have access to. However, please make sure that the user query you generate includes the parameters required to call the API, for which you need to generate random information. 

2. For required parameters like IP address, location, coordinates, etc., provide specific details. For example, instead of simply stating ‘an address’, provide the exact road and district names. 

3. If a required parameter is something like an id or token or code that needs to be obtained from the output of another API, you can use its default value when generating the query. Do not arbitrarily fabricate invalid parameter values, otherwise you will be penalized.

4. When a required parameter is missing in the generated query, simply assign its value as "I don't know". For this exploration, you only need to explore the required parameter values; optional parameter values can be ignored.

#EXAMPLES:
{Example}


# EXAMPLE JSON OUTPUT:
{{
    "User Query": ""
    "Parameters":{{}}
}}
        """
        user = f"""
        Here is the detailed development documentation of an API: 
        {tool_docs}
        Starting below, please give json format output.
        """
        user+="""\nYour output:"""
        messages = [
            {"role": "system","content": system},
            {"role": "user","content":  user},
        ]
        return messages
    
    def explore_api_by_optional(self, tool_docs, Example, previous_user_query):
        system = f"""
Your task is to answer the user's query as best you can. You have access to the tools, which you can use via API call to help with your response:

# GOALS:
It is June 5th, 2025, and many real-time APIs are unable to query historical information. You have already completed the exploration of the necessary parameters for the APIs and generated user questions (which only include the required parameters). You need to do 1) expand on the previously generated questions by adding optional parameters to them. 2) extracting the parameters needed to call these APIs from the generated query, and 3) Here, you can focus on queries that only require calling the API once.

# NOTES:
1. You need to explore optional parameters based on the previously generated query. You should make the query natural - for example, try to avoid using the provided API descriptions or API names in the query, as the user does not know what APIs you have access to. However, please make sure that the user query you generate includes the parameters required to call the API, for which you need to generate random information. 

2. For required parameters like IP address, location, coordinates, etc., provide specific details. For example, instead of simply stating ‘an address’, provide the exact road and district names. 

3. If a required parameter is something like an id or token or code that needs to be obtained from the output of another API, you can use its default value when generating the query. Do not arbitrarily fabricate invalid parameter values, otherwise you will be penalized.

4. When a required parameter is missing in the generated query, simply assign its value as "I don't know". For this exploration, you need to explore both required and optional parameters.

#EXAMPLES:
{Example}

# EXAMPLE JSON OUTPUT:
{{
    "User Query": ""
    "Parameters":{{}}
}}

        """
        user = f"""
Here is the detailed development documentation of an API: 
{tool_docs}
{previous_user_query}
You need to generate relevant questions based on the API documentation, and you can only extract the related parameters from the generated questions.
Starting below, please give json format output.
        """
        user+="""\nYour output:"""
        messages = [
            {"role": "system","content": system},
            {"role": "user","content":  user},
        ]
        return messages
    
    def reflextion_api_params(self,Example,api_query_params):
        system = f"""
Your task is to check whether the generated query and the parameters extracted from it meet the #RULES below based on the API documentation.If the generated query or extracted parameters do not meet the requirements, please clearly state the reason and indicate which specific rule was violated.

# RULES:

## For the User Query:
1. Cross-API Dependent Parameters such as id, token, code, etc. need to be obtained from other APIs, and the user's query can only use the default value in the API document, if the default value does not exist, it cannot be fabricated.
2. The user's query must include all required parameters for calling the API, unless the API documentation does not provide such Cross-API Dependent Parameters.
3. It is May 20th, 2025, and for real-time APIs, time information in the user's query must be set to a date after this.

## For the Extracted Parameters:
4. Parameter values can only be extracted from the user's query, and the format of the parameters must be consistent with the API documentation.User intent does not equate to an explicit parameter value. For example, the user may want the result to be in English, but has not provided the corresponding languagecode for English.
5. The extracted parameters can be unknown, but they cannot be made up.

#EXAMPLES:
{Example}

# EXAMPLE JSON OUTPUT:
{{
    "Reason":{{}}
}}

"""
        user = f"""
        This includes the API documentation, a user query generated based on the documentation, and the corresponding parameters extracted from the query.
        {api_query_params}
"""
        user+="""\nYour output:"""
        messages = [
            {"role": "system","content": system},
            {"role": "user","content":  user},
        ]
        return messages      
