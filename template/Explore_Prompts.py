from dataclasses import dataclass

@dataclass
class ExplorePrompts:
    
    def explore_api_by_required(self, tool_docs, Example):
        system = f"""
Your task is to answer the user's query as best you can. You have access to the tools, which you can use via API call to help with your response:

# Goals:
Now you have the chance to explore the available APIs. You can do this by 1) synthesizing some natural user query that calling the API could help, 2) extracting the parameters needed to call these APIs from the generated query, and 3) Here, you can focus on queries that only require calling the API once.

# Notes:
1. Now, first input your synthesized user query. You should make the query natural - for example, try to avoid using the provided API descriptions or API names in the query, as the user does not know what APIs you have access to. However, please make sure that the user query you generate includes the parameters required to call the API, for which you need to generate random information. 

2. For required parameters like IP address, location, coordinates, etc., provide specific details. For example, instead of simply stating ‘an address’, provide the exact road and district names. 

3. If a required parameter is something like an id or token or code that needs to be obtained from the output of another API, you can use its default value when generating the query. Do not arbitrarily fabricate invalid parameter values, otherwise you will be penalized.

4. When a required parameter is missing in the generated query, simply assign its value as "I don't know". For this exploration, you only need to explore the required parameter values; optional parameter values can be ignored.
Here is an example:
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

# Goals:
You have already completed the exploration of the necessary parameters for the APIs and generated user questions (which only include the required parameters). You need to do 1) expand on the previously generated questions by adding optional parameters to them. 2) extracting the parameters needed to call these APIs from the generated query, and 3) Here, you can focus on queries that only require calling the API once.

# Notes:
1. You need to explore optional parameters based on the previously generated query. You should make the query natural - for example, try to avoid using the provided API descriptions or API names in the query, as the user does not know what APIs you have access to. However, please make sure that the user query you generate includes the parameters required to call the API, for which you need to generate random information. 

2. For required parameters like IP address, location, coordinates, etc., provide specific details. For example, instead of simply stating ‘an address’, provide the exact road and district names. 

3. If a required parameter is something like an id or token or code that needs to be obtained from the output of another API, you can use its default value when generating the query. Do not arbitrarily fabricate invalid parameter values, otherwise you will be penalized.

4. When a required parameter is missing in the generated query, simply assign its value as "I don't know". For this exploration, you need to explore both required and optional parameters.
Here is some examples:
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
        Starting below, please give json format output,
        """
        user+="""\nYour output:"""
        messages = [
            {"role": "system","content": system},
            {"role": "user","content":  user},
        ]
        return messages