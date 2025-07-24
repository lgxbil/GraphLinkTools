QUESATION_REWRITE ="""
#Task:
You are an advanced query rewriter. 
The goal of query rewriting is to supplement potentially implicit but unstated key contextual information to enrich the question's context. Please ensure that during the rewriting process, you avoid adding any extraneous or unrelated details. 
Do not arbitrarily rearrange or combine the original question's logical sequence. At the same time, you must guarantee that the rewritten question comprehensively covers all aspects of the original question without omitting any critical details.

#Rules:
The following are several key points to pay attention to during query rewriting:
1. Date format conversion: "December 17th, 2024" should be converted to "2024-12-17"; "Christmas in 2024" should be converted to "2024-12-25"; "10 AM" converted to 24-hour format "10:00".
2. Date and time reasoning:"rental car on December 1st, 2024, and return it at 4 PM nine days later" should be converted to "rental car on 2024-12-01, and return it 16:00 on 2024-12-10"; "Hotel check-in on November 12, 2024, at 10:00 PM, check-out 56 hours later" should be converted to "check in at the hotel on 2024-11-12 22:00, and check out on 2024-11-15 06:00." To avoid using ambiguous temporal expressions such as "that day" or "the same day,"
3. Clarification of geographical information: "Take flight K99 to London for a trip, and return to Berlin three days later." should be converted to "Depart from Berlin to London via flight K99 for a three-day trip, and then return from London to Berlin by flight". 
4. Note the user's implicit request: "Travel from Seattle to Amsterdam on December 5, 2024, and return on December 12, 2024. Find the cheapest air tickets around those dates" — the user wants to search for round-trip tickets, and the travel dates are not strictly fixed.

#Examples:
Query: Today is October 13th, 2024. I want to rent a car for a day at the San Diego Marriott La Jolla. Could you compare the price differences for picking up the car at 8 AM tomorrow and the day after tomorrow at the same place for a 24-hour rental?
{
    "written question":"Today is 2024-10-13. I want to rent a car for a 24-hour period from the San Diego Marriott La Jolla. Please compare the price differences for these two options:Pick up the car at 2024-10-14 08:00 and return it at 2024-10-15 08:00;Pick up the car at 2024-10-15 08:00 and return it at 2024-10-16 08:00"
}

Query: I want to find out about the cheapest connecting flight leaving from Boston on December 15, 2024, going to Philadelphia and Washington, then returning to Boston. I'm expecting to stay in each city for seven days. My address is 800 Boylston St in Boston. Can you book a taxi to take me to the airport three hours before the flight takes off and bring me home one hour after the returning flight lands? 
{
    "written question":"I want to find the cheapest multi-city flight itinerary with the following schedule:Depart from Boston to Philadelphia on 2024-12-15;Depart from Philadelphia to Washington on 2024-12-22;Return from Washington to Boston on 2024-12-29.Once the flight details are confirmed, My address is 800 Boylston St in Boston. Can you book a taxi to take me to the airport three hours before the flight takes off and bring me home one hour after the returning flight lands?"
}

Query: It's now 2 o'clock on November 12th, 2024 and I'm at Toronto Pearson International Airport. I hope to rent a car to visit the most trending attraction in Toronto and return it near the attraction 26 hours later.
{
    "written question":"The current time is 2024-11-12 14:00, and I am at Toronto Pearson International Airport. I want to rent a car to visit the most trending attraction in Toronto and return the car near that attraction at 2024-11-13 16:00. Please help me with car rental options and the recommended trending attraction."
}

Query: My friend Lily is going to rent a car at Dallas-Fort Worth International Airport at 7 AM on November 20th, 2024, and return it at George Bush Intercontinental Airport in Houston at 1 PM nine days later. Provide detailed information about two different car types.
{
    "written question": "My friend Lily plans to rent a car at Dallas-Fort Worth International Airport at 07:00 on 2024-11-20, and return it at George Bush Intercontinental Airport in Houston at 13:00 on 2024-11-29. Please provide detailed information about two different car types available for this rental."
}

Query:Check if tickets are available for the two most trending attractions in New York on any Tuesday in September 2024.
{
    "written question":"Please check ticket availability for the two most trending attractions in New York on any Tuesday in September 2024, specifically on 2024-09-03, 2024-09-10, 2024-09-17, and 2024-09-24."
}

Query: I need a multi-stop flight itinerary with the following schedule: Depart from Berlin to London on 2024-11-18 for a three-day business trip, then travel to a nearby city (unspecified) for a two-day vacation, and finally return from that nearby city to Berlin. Please look up flight options that fit this schedule.
{
    "written question": "I will fly from Berlin to London for a three-day business trip starting on 2024-11-18. After that, I will travel by ground transportation to a London nearby city for a two-day leisure visit. Finally, I will fly to Berlin directly from that nearby city on 2024-11-23. Could you look up multi-stop flights that fit this itinerary?"
}

End of reference examples

#Notes
1. Be sure to note that when rewriting the question, avoid adding any extraneous additional questions. Ensure the rewritten question fully encompasses all aspects of the original question without omitting any key details.
2. Do not over-interpret time and location information. Eg.subsequent action times cannot be confirmed without obtaining the exact flight arrival time. Airports cannot be determined solely by city names, as a city may have multiple airports.

#Output Format
Please output in the following JSON format that can be parsed by Python's json.loads function. Do not answer the question, provide any explanation, or output any other information.
{
    "written question": "Rewritten question"
}
"""

QUESATION_REWRITE_USER = """
#Input
Please rewrite the following question: 
{question}
"""

API_ARGS_FILL = """
#Task
You are an API parameter filling expert. The user's query needs to call a series of APIs to be answered, and your task is to extract the API parameter information from the query.

#Parameter Filling Guidelines:
1. Only Fill in the parameters of the APIs that are relevant to the question: Some of the provided APIs are unrelated to the question.
2. API parameters can only be sourced from the query: Do not arbitrarily infer parameters. For example, if the question only mentions taking off from Beijing, do not infer airport parameters on your own. Making arbitrary inferences about information that is not present in the query will result in punishment.
4. The required parameters of the API must be filled in: If the required parameters of the API cannot be extracted from the query, they should be filled with "unkown(Explanation for the unknown)".
5. Optional parameters should be filled based on the content of the question: If an optional parameter that needs to be filled cannot extract information that meets the parameter requirements from the user intent and needs to be obtained from other APIs, it should be temporarily filled in as "unknown(Explanation for the unknown)".
6. Parameters not mentioned in the user intent should be filled with null. For parameters mentioned in the user intent but whose values are temporarily unknown and need to be obtained from the output of other APIs, they should be filled with unknown (Explanation for the unknown).

#Examples:
Query:
Today is 2024-10-13. I want to rent a car for a 24-hour period from the San Diego Marriott La Jolla. Please compare the price differences for these two options:Pick up the car at 2024-10-14 08:00 and return it at 2024-10-15 08:00;Pick up the car at 2024-10-15 08:00 and return it at 2024-10-16 08:00.
API_INFO:
Search_Car_Rentals
Output:
[
    {
        "api_name": "Search_Car_Rentals", 
        "arguments": {
            "pick_up_latitude": "unknown(don't know the pick_up_latitude of San Diego Marriott La Jolla, Need to retrieve from another API)",
            "pick_up_longitude": "unknown(don't know the pick_up_longitude of  San Diego Marriott La Jolla., Need to retrieve from another API)",
            "drop_off_latitude": "unknown(don't know the drop_off_latitude of the drop-off location San Diego Marriott La Jolla, Need to retrieve from another API)",
            "drop_off_longitude": "unknown(don't know the drop_off_longitude of the drop-off location San Diego Marriott La Jolla,Need to retrieve from another API)",
            "pick_up_date": "2024-10-14",
            "drop_off_date": "2024-10-15",
            "pick_up_time": "08:00",
            "drop_off_time": "08:00"
        }
    },
    {
        "api_name": "Search_Car_Rentals", 
        "arguments": {
            "pick_up_latitude": "unknown(don't know the pick_up_latitude of the pick-up location San Diego Marriott La Jolla, Need to retrieve from another API)",
            "pick_up_longitude": "unknown(don't know the pick_up_longitude of the pick-up location San Diego Marriott La Jolla., Need to retrieve from another API)",
            "drop_off_latitude": "unknown(don't know the drop_off_latitude of the drop-off location San Diego Marriott La Jolla, Need to retrieve from another API)",
            "drop_off_longitude": "unknown(don't know the drop_off_longitude of the drop-off location San Diego Marriott La Jolla,Need to retrieve from another API)",
            "pick_up_date": "2024-10-15",
            "drop_off_date": "2024-10-16",
            "pick_up_time": "08:00",
            "drop_off_time": "08:00"
        }
    }
]
Query:
"I will fly from Berlin to London for a three-day business trip starting on 2024-11-18. After that, I will travel by ground transportation to a nearby city for a two-day leisure visit. Finally, I will fly to Berlin directly from that nearby city on 2024-11-23. Could you look up multi-stop flights that fit this itinerary?"
API_INFO:
Search_Flights_Multi_Stops
Output:
[
    {
        "api_name": "Search_Flights_Multi_Stops",
        "arguments": {
            "legs": [
                {
                    "fromId": "unknown(Berlin airport fromId needs to be retrieved from another API)",
                    "toId": "unknown(London airport toId needs to be retrieved from another API)",
                    "date": "2024-11-18"
                },
                {
                    "fromId": "unknown(nearby city not specified and fromId dont know)",
                    "toId": "unknown(Berlin airport toId needs to be retrieved from another API)",
                    "date": "2024-11-23"
                }
            ],
            "pageNo": null,
            "adults": null,
            "children": null,
            "sort": null,
            "cabinClass": null,
            "currency_code": null
        }
    }
]
Query: 
Our company is planning to hold a conference in Seattle from December 10th to December 20th, 2024. Find three hotels close to Pike Place Market with airport shuttles and check the detailed information and payment methods for these hotels.
API_INFO:
Search_Flight
Output:
[]
End of reference examples

#Output Format
Please output in the following JSON format that can be parsed by Python's json.loads function.If the currently provided API is unrelated to the question, directly return an empty list.
[
    {
        "api_name": "API_NAME",
        "arguments": {
            "param_name": "value from query/ unkonwn(Explanation for the unknown) / null"
        }
    }
]

#Note: Do not make assumptions about the "search_type" and "categories_filter" parameters. These values need to be retrieved from other APIs.
"""
API_ARGS_FILL_USER = """
#Input
Please fill in the API parameters according to the Query and API information. You only fill in the APIs provided below. Do not invent or fabricate any other APIs, or you will be penalized.If the currently provided API is unrelated to the question, directly return an empty list.
Query:
{question}
API_INFO:
{api_info}
Output:
"""

JUDGE_LINK = """
#Task
You are an advanced business process analyzer. In the business process, each node represents an independent API call. You will be provided with the following information: "The user's question", "Existing API Call Nodes", "A target API call" and "Target API Infomation". Your task is to identify the upstream API calls from the given nodes that can serve as dependencies for the target API's unresolved parameters, thereby completing the parameter sourcing path.

#Rules:
1. You need to analyze the user's query to understand their intent and the purpose of the target API call.
2. You can only select dependency APIs for the target API's unresolved parameters from the given "Existing API Call Nodes". If no suitable nodes exist, leave the "param value" as unkown(Explanation for the unknown).
3. For the selected node, do not make any modifications. Directly fill the node into the corresponding parameters.

Examples:

(Example 1 starts)
Query:
"I will fly from Berlin to London for a three-day business trip starting on 2024-11-18. After that, I will travel by ground transportation to a nearby city for a two-day leisure visit. Finally, I will fly to Berlin directly from that nearby city on 2024-11-23. Could you look up multi-stop flights that fit this itinerary?"
API call nodes description:
[]
Existing API Call Nodes:
[
    Search_Flight_Location(query = "Berlin"),
    Search_Flight_Location(query = "London"),
    
]
Target API's information:
{
    "api_name": "Search_Flights_Multi_Stops",
    "params_dependencies": {
        "legs[].fromId": [
            {
                "source_api": "Search_Flight_Location",
                "source_api_respath": "$[0].id",
            }
        ],
        "legs[].toId": [
            {
                "source_api": "Search_Flight_Location",
                "source_api_respath": "$[0].id",
            }
        ],
    }
}
Target API call:
{
    "api_name": "Search_Flights_Multi_Stops",
    "arguments": {
        "legs": [
            {
                "fromId": "unknown(Airport ID for Berlin, needs to be retrieved from other API)",
                "toId": "unknown(Airport ID for London, needs to be retrieved from other API)",
                "date": "2024-11-18"
            },
            {
                "fromId": "unknown(Airport ID for the nearby city, city name not provided in the query, needs to be retrieved from user or other APIs)",
                "toId": "unknown(Airport ID for Berlin, needs to be retrieved from Sother API)",
                "date": "2024-11-23"
            }
        ]
    }
}

OUTPUT:
{
    "api_name": "Search_Flights_Multi_Stops",
    "arguments": {
        "legs": [
            {
                "fromId": "Search_Flight_Location(query = \"Berlin\")",
                "toId": "Search_Flight_Location(query = \"London\")",
                "date": "2024-11-18"
            },
            {
                "fromId": "unknown(Airport ID for the nearby city, city name not provided in the query, needs to be retrieved from user or other APIs)",
                "toId": "Search_Flight_Location(query = \"Berlin\")",
                "date": "2024-11-23"
            }
        ]
    }
}
(Example 1 ends)

End of reference examples

#OUTPUT FORMAT:
Please output in the following JSON format that can be parsed by Python's json.loads function.
{
    "api_name": "API_NAME",
    "arguments": {
        "param_name": "API call node / unkonwn(Explanation for the unknown)"
    }
}
Note: The upstream nodes used to fill in parameters must only come from the nodes provided in the Existing API Call Nodes. Do not create or fabricate new nodes at will, otherwise you will be penalized. 
"""
JUDGE_LINK_USER = """
Query:
{question}
A list of API call nodes:
{api_nodes}
Target API's information:
{target_api_description}
Target API call:
{target_api_call}
OUTPUT:
"""

FIND_UPSTREAM_API = """
You are an expert in analyzing API dependencies. You will be given a user's question and a target API call node, where some of the parameters are unknown. You will also receive additional API related to target API call.

#Task
Your task is to analyze the user's question and the provided information to identify which "Source APIs" should be called first to retrieve the unknown parameters. The goal is to complete the full API call chain needed to successfully invoke the target API.

#Rules:
1. First, analyze the user's question to understand the purpose of the target API call and identify which parameters are unknown.If a parameter in the target API comes from another API call, it should not be treated as an unknown parameter.
2. Then, select relevant APIs from the provided list that can serve as upstream APIs to supply the unknown parameters for the target API.
3. API parameters can only be sourced from the query: Do not arbitrarily infer parameters. For example, if the question only mentions taking off from Beijing, do not infer airport parameters on your own. Making arbitrary inferences about information that is not present in the query will result in punishment.
4. The required parameters of the API must be filled in: If the required parameters of the API cannot be extracted from the query, they should be filled with "unkown(Explanation for the unknown)".
5. Optional parameters should be filled based on the content of the question: If the optional parameters of the API cannot be extracted from the query, they should be filled with "unkown(Explanation for the unknown)". If the optional parameters are not needed to solve the user's problem, fill them with "null" to indicate that the default values will be used.
6. Parameters not mentioned in the user intent should be filled with null. For parameters mentioned in the user intent but whose values are temporarily unknown and need to be obtained from the output of other APIs, they should be filled with unknown (Explanation for the unknown).

#Examples:

(Example 1 starts)
Query:"I will fly from Berlin to London for a three-day business trip starting on 2024-11-18. After that, I will travel by ground transportation to a nearby city for a two-day leisure visit. Finally, I will fly to Berlin directly from that nearby city on 2024-11-23. Could you look up multi-stop flights that fit this itinerary?"

Related API List:
[
    {
        "name": "Search_Flight_Location",
        "func_description": "Find airports by their location, address, state, country, etc.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "String",
                    "description": "Names of airport, locations, cities, districts, places, countries, counties etc.",
                    "example_value": "new",
                    "required": true
                },
                "languagecode": {
                    "type": "String",
                    "description": "To obtain the response data in a specific language, enter the languagecode.",
                    "example_value": "",
                    "required": false
                }
            },
            "required": [
                "query"
            ]
        }
    }
]
Target API call:
{
    "api_name": "Search_Flights_Multi_Stops",
    "arguments": {
        "legs": [
            {
                "fromId": "Search_Flight_Location(query = \\"Berlin\\")(Airport ID for Berlin, needs to be retrieved from Search_Flight_Location)",
                "toId": "Search_Flight_Location(query = \\"London\\")(Airport ID for London, needs to be retrieved from Search_Flight_Location)",
                "date": "2024-11-18"
            },
            {
                "fromId": "unknown(Airport ID for the nearby city, city name not provided in the query, needs to be retrieved from user or other APIs)",
                "toId": "Search_Flight_Location(query = \\"Berlin\\")(Airport ID for Berlin, needs to be retrieved from Search_Flight_Location)",
                "date": "2024-11-23"
            }
        ]
    }
}
Output:
[
    {
        "target_args": "legs[1].fromId",
        "source_api_name": "Search_Flight_Location",
        "arguments": {
            "query": "unknown(City name for the nearby city, needs to be retrieved from user or other APIs)"
        }
    }
]
(Example 1 ends)

Output Format:
Please output in the following JSON format that can be parsed by Python's json.loads function.
[
    {
        "target_args": "unkwnown_param",
        "source_api_name": "API_NAME",
        "arguments": {
            "param_name": "value from query / unkonwn(Explanation for the unknown) / null"
        }
    }
]
Note: When constructing the parameter dependency chain, if a parameter field of the target API has already been assigned a value from an existing API call, it indicates that the upstream dependency for this field has been satisfied, and there is no need to create a duplicate upstream node. Only when the parameter value is unknown(...) should you continue to identify or create its upstream data source.If you create duplicate API call nodes, you will be penalized.
"""
FIND_UPSTREAM_API_USER = """
Query:
{question}
Related API List:
{related_api_list}
Target API description:
{target_api_description}
Target API call:
{target_api_call}
Output:
"""

QUESATION_DECOMPOSE = """
#Task
You are a task decomposition expert responsible for breaking down a complex user query into multiple programmable subtasks. You will receive a complex problem that requires calling external APIs to solve, along with the edges of the call flow generated from the problem (each edge includes a source node, a target node, and the information passed between nodes). Please decompose the problem reasonably based on the call flow.

#Decomposition Rules:
1. Understand the user query and the overall call flow by analyzing the edge information.
2. Split by API Count:Each subtask should use no more than three distinct APIs. You may split the problem into up to three subtasks.
3. Split by Semantic Boundaries:If the user query contains semantic requests like “summarize,” “aggregate,” “recommend,” or other tasks that are difficult to implement through direct API calls, use these as natural split points for subtasks.
4. Respect Dependency Relationships:When splitting subtasks, follow the API call dependencies shown in the flowchart. Do not skip required upstream calls. Ensure the call order in each subtask is logically correct and consistent with the data flow.


#Examples:
Query: 
"My wife and I plan to travel from Edinburgh to Lisbon on 2024-11-20 to visit Sintra. Please check the fastest flight from Edinburgh to Lisbon on 2024-11-20 and the start time of the Sintra tour on the same day, 2024-11-20. If the flight's arrival time does not allow us to join the Sintra tour on 2024-11-20, please provide the start time of the Sintra tour on the next day, 2024-11-21."
Call Flow Edges:
[
    {
        "from_api": Search_Flight_Location("query": "Milan"), 
        "response_path":"$[].id", 
        "target_param": "fromId",
        "to_api": Search_Flights("fromId": unknown("Departure airport ID not provided in the query"), "toId": unknown("Destination airport ID not provided in the query"), "departDate": "2024-11-20", "sort": "FASTEST")"
    },
    {
        "from_api": Search_Attraction_Location("query": "Edinburgh Castle"),
        "response_path":"$.products[].productSlug",
        "target_param": "slug",
        "to_api": Get_Availability("slug": unknown("Attraction identifier slug not provided in the query"), "date": "2024-11-20")
    },
    {
        "from_api": Search_Attraction_Location("query": "Edinburgh Castle"),
        "response_path":"$.products[].productSlug",
        "target_param": "slug",
        "to_api": Get_Availability("slug": unknown("Attraction identifier slug not provided in the query"), "date": "2024-11-21")
    }
    {
        "from_api": Search_Flight_Location("query": "Edinburgh"),
        "response_path":"$[].id",
        "target_param": "toId",
        "to_api": Search_Flights("fromId": unknown("Departure airport ID not provided in the query"), "toId": unknown("Destination airport ID not provided in the query"), "departDate": "2024-11-20", "sort": "FASTEST")
    }
]
Relateded APIs Information:
[]
Output:
{
  "subtask_1": {
    "description": "By calling Search_Flight_Location to get the airport IDs of Edinburgh and Lisbon, and passing them into Search_Flights as the fromId and toId parameters, the purpose of this subtask is to search for the fastest flight from Edinburgh to Lisbon on 2024-11-20, obtain the flight arrival time, and provide data for the subsequent decision on whether the Edinburgh Castle tour can be joined on the same day.",
    "related_call_edges": [
      {
        "from_api": "Search_Flight_Location(\"query\": \"Edinburgh\")",
        "response_path": "$[].id",
        "target_param": "fromId",
        "to_api": "Search_Flights(\"fromId\": unknown(\"Departure airport ID not provided in the query\"), \"toId\": unknown(\"Destination airport ID not provided in the query\"), \"departDate\": \"2024-11-20\", \"sort\": \"FASTEST\")"
      },
      {
        "from_api": "Search_Flight_Location(\"query\": \"Lisbon\")",
        "response_path": "$[].id",
        "target_param": "toId",
        "to_api": "Search_Flights(\"fromId\": unknown(\"Departure airport ID not provided in the query\"), \"toId\": unknown(\"Destination airport ID not provided in the query\"), \"departDate\": \"2024-11-20\", \"sort\": \"FASTEST\")"
      }
    ]
  },
  "subtask_2": {
    "description": "The purpose of this subtask is to check the available start times of the Edinburgh Castle tour on 2024-11-20 and 2024-11-21, determine whether the flight arrival time allows participation in the same-day tour, and obtain an alternative start time for the next day if the same-day tour is not feasible.",
    "related_call_edges": [
      {
        "from_api": "Search_Attraction_Location(\"query\": \"Edinburgh Castle\")",
        "response_path": "$.products[].productSlug",
        "target_param": "slug",
        "to_api": "Get_Availability(\"slug\": unknown(\"Attraction identifier slug not provided in the query\"), \"date\": \"2024-11-20\")"
      },
      {
        "from_api": "Search_Attraction_Location(\"query\": \"Edinburgh Castle\")",
        "response_path": "$.products[].productSlug",
        "target_param": "slug",
        "to_api": "Get_Availability(\"slug\": unknown(\"Attraction identifier slug not provided in the query\"), \"date\": \"2024-11-21\")"
      }
    ]
  }
}

Output Format:
Please output in the following JSON format that can be parsed by Python's json.loads function. The related calls (related_call) for the subtask must be selected only from the provided Call Flow Edges.If you fabricate related call edges, you will be penalized.
{
    "subtask_1": {
        "description":"An easy-to-program description combining the problem and the call flow edges",
        "related_call_edges":[
            {
                "from_api": "",
                "response_path": "",
                "target_param": "",
                "to_api": ""
            },
        ]
    }
}
"""
QUESATION_DECOMPOSE1 = """
#Task
You are a task decomposition expert responsible for breaking down a complex user query into multiple programmable subtasks. You will receive a complex user query that requires calling a series of APIs to solve. Additionally, you need to provide a call flow diagram (including nodes and edges) as auxiliary information to help decompose the problem.

#Decomposition Rules:
1. Understand the user query and the overall call flow diagram.
2. Split by API Count:Each subtask should use no more than three distinct APIs. You may split the problem into up to three subtasks.
3. Split by Semantic Boundaries:If the user query contains semantic requests like “summarize,” “aggregate,” “recommend,” or other tasks that are difficult to implement through direct API calls, use these as natural split points for subtasks.
4. Respect Dependency Relationships:When splitting subtasks, follow the API call dependencies shown in the flowchart. Do not skip required upstream calls. Ensure the call order in each subtask is logically correct and consistent with the data flow.


#Examples:
Query: 
"My wife and I plan to travel from Edinburgh to Lisbon on 2024-11-20 to visit Sintra. Please check the fastest flight from Edinburgh to Lisbon on 2024-11-20 and the start time of the Sintra tour on the same day, 2024-11-20. If the flight's arrival time does not allow us to join the Sintra tour on 2024-11-20, please provide the start time of the Sintra tour on the next day, 2024-11-21."
Call Node:
[
    Search_Flight_Location("query": "Milan"),
    Search_Flight_Location("query": "Edinburgh"),
    Search_Attraction_Location("query": "Edinburgh Castle"),
    Search_Flights("fromId": unknown("Departure airport ID not provided in the query"), "toId": unknown("Destination airport ID not provided in the query"), "departDate": "2024-11-20", "sort": "FASTEST"),
    Get_Availability("slug": unknown("Attraction identifier slug not provided in the query"), "date": "2024-11-20"),
    Get_Availability("slug": unknown("Attraction identifier slug not provided in the query"), "date": "2024-11-21"),
]

Call Flow Edges:
[
    {
        "from_api": Search_Flight_Location, 
        "response_path":"$[].id", 
        "target_param": "fromId",
        "to_api": Search_Flights
    },
    {
        "from_api": Search_Attraction_Location,
        "response_path":"$.products[].productSlug",
        "target_param": "slug",
        "to_api": Get_Availability
    },
    {
        "from_api": Search_Flight_Location,
        "response_path":"$[].id",
        "target_param": "toId",
        "to_api": Search_Flights,
    }
]
Relateded APIs Information:
[]
Output:
{
  "subtask_1": {
    "description": "By calling Search_Flight_Location to get the airport IDs of Edinburgh and Lisbon, and passing them into Search_Flights as the fromId and toId parameters, the purpose of this subtask is to search for the fastest flight from Edinburgh to Lisbon on 2024-11-20, obtain the flight arrival time, and provide data for the subsequent decision on whether the Edinburgh Castle tour can be joined on the same day.",
    "Node":[
        Search_Flight_Location("query": "Milan"),
        Search_Flight_Location("query": "Edinburgh"),
        Search_Flights("fromId": unknown("Departure airport ID not provided in the query"), "toId": unknown("Destination airport ID not provided in the query"), "departDate": "2024-11-20", "sort": "FASTEST"),
    ]
    "Edges":[
        {
            "from_api": Search_Flight_Location, 
            "response_path":"$[].id", 
            "target_param": "fromId",
            "to_api": Search_Flights
        },
        {
            "from_api": Search_Flight_Location,
            "response_path":"$[].id",
            "target_param": "toId",
            "to_api": Search_Flights,
        },
    ]
  },
  "subtask_2": {
    "description": "The purpose of this subtask is to check the available start times of the Edinburgh Castle tour on 2024-11-20 and 2024-11-21, determine whether the flight arrival time allows participation in the same-day tour, and obtain an alternative start time for the next day if the same-day tour is not feasible.",
    "Node":[
        Search_Attraction_Location("query": "Edinburgh Castle"),
        Get_Availability("slug": unknown("Attraction identifier slug not provided in the query"), "date": "2024-11-20"),
        Get_Availability("slug": unknown("Attraction identifier slug not provided in the query"), "date": "2024-11-21"),
    ],
    "Edges":[
        {
            "from_api": Search_Attraction_Location,
            "response_path":"$.products[].productSlug",
            "target_param": "slug",
            "to_api": Get_Availability
        },
    ]
  }
}

Output Format:
Please output in the following JSON format that can be parsed by Python's json.loads function. The related calls (related_call) for the subtask must be selected only from the provided Call Flow Edges.If you fabricate related call edges, you will be penalized.
{
    "subtask_1": {
        "description":"An easy-to-program description combining the problem and the call flow edges",
        "Nodes":[],
        "Edges":[],
    }
}
Note:You must select nodes and edges only from the given "Call Node" and "Call Flow Edges". If you fabricate any on your own, you will be penalized.
"""

QUESATION_DECOMPOSE_USER = """
#Input
Query: 
{question}
Call Flow Edges:
{call_flow_edges}
Relateded APIs Information:
{related_api_information}
Output:
"""

QUESATION_DECOMPOSE_USER1= """
#Input
Query: 
{question}
Nodes:
{nodes}
Edegs:
{edges}
Output:
"""






CODE_CLASS = """
You are a programming expert. Use Python to solve the problem described by the user. Based on the given tools and workflow, generate a complete Python code block (as a string) that can be directly executed in a Jupyter Notebook using InteractiveShell.instance().run_cell().

#Code Style and Specification Requirements:
1. Output the complete code as a Python string, ensuring it can be correctly executed by InteractiveShell.instance().run_cell(). 

2. Tool invocation standards: Tools should be invoked using function calls, for example: result = F.tool_name(params). Before each tool invocation, clearly define the parameters to be used, with variable names that clearly convey their meaning.

3. Tool Response Exception Handling Standard:
After each API call, it is required to check whether the request was successful. If not, an exception with the error message must be raised. 

4. Tool response handling standards: 
- When processing API responses, refer to the specified response_path in the workflow diagram and the response format in the API documentation to accurately extract the target fields. 
- For cases where no specific filtering method is specified, default to taking the first element at each level of the array. 
- If a filtering requirement is specified, filter according to the requirement to extract the optimal element. For example, the Search_Flights(departDate=2025-7-1, sort="FASTEST") API is already sorted by the fastest flights, so you can directly take the first flight from the results. 
- However, the Get_Room_Availability("hotel_id": "521") API may require filtering by price to extract the room with the lowest price.

5. At the end of the code, use print() to output the information with explanatory text. If the subtask requires summarization or comparison, you can directly print the complete response.

#Examples:
{CODE_EXAMPLE}

#Output Format
```python
import necessary lib
{{code}}
```
#Note:Follow the code style in the example.There is no need to define def functions.You can directly use the form result = F.tool_name(params) to invoke the tool.
"""
#例子提供比较难的部分todo
CODE_EXAMPLE = """
(Example 1 starts)

Query:
Search for the fastest flight from Edinburgh to Lisbon on 2024-11-20. Obtain the flight arrival time, and provide data for the subsequent decision on whether the Edinburgh Castle tour can be joined on the same day.
Output:
```python
# Step 1: Get Edinburgh airport ID
search_edinburgh_params = {'query': 'Edinburgh'}
edinburgh_location_result = F.Search_Flight_Location(search_edinburgh_params)

# Check API response status
if not edinburgh_location_result.get('status'):
    raise Exception(f"Search_Flight_Location failed: {edinburgh_location_result.get('message', 'Unknown error')}")

from_id = edinburgh_location_result['data'][0]['id']  # Get result from data field

# Step 2: Get Lisbon airport ID
search_lisbon_params = {'query': 'Lisbon'}
lisbon_location_result = F.Search_Flight_Location(search_lisbon_params)

if not lisbon_location_result.get('status'):
    raise Exception(f"Search_Flight_Location failed: {lisbon_location_result.get('message', 'Unknown error')}")

to_id = lisbon_location_result['data'][0]['id']

# Step 3: Search for the fastest flight
search_flights_params = {
    'fromId': from_id,
    'toId': to_id,
    'departDate': '2024-11-20',
    'sort': 'FASTEST'
}
flight_search_result = F.Search_Flights(search_flights_params)

if flight_search_result.get('status'):
    raise Exception(f"Search_Flights failed: {flight_search_result.get('message', 'Unknown error')}")

# Extract arrival time
fastest_flight = flight_search_result['data']['flightOffers'][0]  # Note data is under 'data' field
arrival_time = fastest_flight['segments'][0]['arrivalTime']

# Return final result
print(f"Fastest flight from Edinburgh to Lisbon on 2024-11-20 arrives at: {arrival_time}")
```
(Example 1 ends)

(Example 2 starts)
Query:Retrieve the destination ID for Canberra and the categories filter for family rooms that allow pets. This subtask involves calling Search_Hotel_Destination to get the dest_id for Canberra and then using Get_Filter to retrieve the appropriate categories_filter.
Output
```python
# Step 1: Retrieve destination ID for Canberra
search_destination_query = "Canberra"
search_destination_params = {
    "query": search_destination_query
}
canberra_destination_result = F.Search_Hotel_Destination(**search_destination_params)

# Error handling
if not destination_response:
    raise Exception(f"Search_Hotel_Destination failed or unexpected format: {canberra_destination_result.get('message', 'Unknown error')}")

# Extract dest_id
first_dest = destination_response[0]
dest_id = first_dest.get("dest_id")
if not dest_id:
    raise Exception(f"No dest_id found in response: {first_dest}")

# Step 2: Call Get_Filter to retrieve filters
get_filter_params = {
    "dest_id": dest_id,
    "search_type": "city",
    "arrival_date": "2024-11-15",
    "departure_date": "2024-11-22",
    "adults": 2,
    "children_age": "4,9",
    "room_qty": 1,
}
filter_result = F.Get_Filter(**get_filter_params)

# Error handling
if not filter_result:
    raise Exception(f"Get_Filter failed or unexpected format: {canberra_destination_result.get('message', 'Unknown error')}")

# Step 3: Extract genericIds for 'family' and 'pet' related options
family_id = None
pet_id = None
for filt in filter_result["filters"]:
    title = filt.get("title", "").lower()
    for opt in filt.get("options", []):
        option_title = opt.get("title", "").lower()
        generic_id = opt.get("genericId")
        if not generic_id:
            continue
        # Identify family rooms by 'family' keyword
        if "family" in option_title and family_id is None:
            family_id = generic_id
        # Identify pet-friendly rooms by 'pet' keyword
        if "pet" in option_title and pet_id is None:
            pet_id = generic_id

if family_id is None or pet_id is None:
    raise Exception(f"Could not find both family_id and pet_id in filters: {json.dumps(filter_response, indent=2)}")

# Combine into categories_filter string
categories_filter = f"{family_id},{pet_id}"

# Final output
print(f"Destination ID for Canberra: {dest_id}")
print(f"Retrieved categories_filter for family & pet-friendly rooms: {categories_filter}")

(Example 2 ends)

"""

CODE_CLASS_USER = """
Query: 
{question}
Relateded APIs Information:
{related_api_information}
Output:
"""

ERROR_ANALYSIS= """
You are an expert in analyzing code execution errors. You will receive a user problem that needs to be solved by calling a series of APIs, along with the corresponding code and the execution error messages. Based on the user's problem and the API information, you need to provide suggestions for correcting the code.

1. You need to analyze the cause of the error based on the user's question, the API parameters, and the response format, and provide suggestions for modifying the code.

#Example
{error_example}

Output:
<<Your Suggestion>>
"""

ERROR_ANALYSIS_USER = """
Query:
{query}
Code:
{code}
Error:
{error_info}
API_INFO:
{api_info}
"""

error_example = """
(Example 1 Start)
Query:
Please check the detailed information of the fastest flight from Guangzhou to Los Angeles on 2024-12-10, and also verify the availability of hotels within 30 kilometers of Los Angeles International Airport on the same day.
Code:
Search_Hotels_By_Coordinates(arrival_date = "2024-12-10", departure_date = "2024-12-10", "latitude" = 29.1111, "longitude" = 111.1111, "radius" = 30)
Error:
departure_date does not match the actual value.
API_INFO:
[]
OUTPUT:
The question did not mention the hotel departure_date date; it only mentioned searching for a hotel on the same day as the flight on 2024-12-10. Therefore, it can only be assumed by default that the stay is for one night, with the departure_date date on 2024-12-11.
(Example 1 End)
"""

