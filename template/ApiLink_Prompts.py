from dataclasses import dataclass
import json

@dataclass
class ApiLinkPrompts:
    def response_filter_one(self, target_api_info, target_api_params, api_response_fields):
        system = f"""
You are a professional API Dependency Evaluator. Your task is to analyze whether response fields from source APIs can serve as valid input parameters for a target API, return the top 30 most relevant results. Based on:
Semantic relevance(e.g., user_id → userId).
Contextual alignment (ignore mismatches like latitude for a username field).

#Input Format
1. Target API Documentation
2. Target Parameters Of Target API(One input parameter you need to focus on)
3. List of Some Source API Resopnse Fields



#OUTPUT JSON FORMAT:
[{{
    "api_name1": "api_response_fields",
}},
...
{{
    "api_name10": "api_response_fields"
}}]
"""
        user = f"""
Target API Documentation:
{target_api_info}
Target Parameters Of Target API:
{target_api_params}
List of Some Source API Fields:
{api_response_fields}

"""
        messages = [
            {"role": "system","content": system},
            {"role": "user","content":  user},
        ]
        
        return messages
    
    def response_filter_fine_grained(self, target_api_info, target_api_params,api_response_fields):
        system = f"""
#ROLE:
You are a professional API Dependency Evaluator. Your task is to analyze whether response fields from source APIs can serve as valid input parameters for a target API.

#INPUT:
1. Target API Documentation
2. Target Parameters Of Target API(One input parameter you need to focus on)
3. Dict of an API Resopnse Field

#RULES:
1. First, determine whether a business-association is formed due to the fields of the source API and the parameters of the target API, or whether it is a necessary prerequisite API for calling the target API.Meeting any one of them is sufficient.
2. Determine which specific field of the API can be used as input for the target parameters of target api.
3. Pay attention to whether the data type of the API's response field matches the data type of the target API's parameter.However, sometimes even though the data types do not match exactly, the response field of the source API may contain the information required by the target API parameter. For example, a field with the format "yyy-mm-dd Hh-Mm" may include the value needed for the pickUpTime parameter (which expects the format "24-Hour Hh:Mm"). In such cases, it is important to carefully examine the example values from the response fields to determine if they can be appropriately adapted or extracted for use as input parameters.


#EXAMPLE1:
Target API Documentation:
{{
    "name": "Search_Flights",
    "endpoint": "/api/v1/flights/searchFlights",
    "func_description": "Search Flights. ",
    "parameters": {{
        "type": "object",
        "properties": {{
            "fromId": {{
                "type": "String",
                "description": "From/Departure location Id. fromId can be retrieved from api/v1/flights/searchDestination(Search Flight Location) endpoint in Flights collection as id.",
                "example_value": "BOM.AIRPORT",
                "required": true
            }},
            "toId": {{
                "type": "String",
                "description": "To/Arrival location Id. toId can be retrieved from api/v1/flights/searchDestination(Search Flight Location) endpoint in Flights collection as id.",
                "example_value": "DEL.AIRPORT",
                "required": true
            }},
            "departDate": {{
                "type": "Date (yyyy-mm-dd)",
                "description": "Departure or travel date.\nFormat: YYYY-MM-DD",
                "example_value": "",
                "required": true
            }},
        }}
    }}
}}
Target Parameters Of Target API:
"departDate": {{
    "type": "Date (yyyy-mm-dd)",
    "description": "Departure or travel date.\nFormat: YYYY-MM-DD",
    "example_value": "",
    "required": true
}},
Dict of A Source API Resopnse Field:
{{
    "from_api":"Get_Room_Availability",
    "api_desc":"This API is ideal for travelers and booking platforms checking hotel availability and pricing. It retrieves real-time room rates and stay requirements for specified dates, allowing users to compare costs and plan stays. The response includes daily pricing, minimum stay duration, and supports filtering by room quantity and guest count. The hotel ID must be obtained from the SearchHotels API.",
    "example_value":[{{
        "$.avDates[*].date":"2025-06-12"
    }}]
}}
OUTPUT:
{{
    "reason": "While the APIs serve different functions, there's a logical business relationship where travelers commonly use hotel availability dates to determine their flight booking dates. The 'avDates[].date' field from 'Get_Room_Availability' perfectly matches the 'Date (yyyy-mm-dd)' format required by 'departDate' in 'Search_Flights'. This represents a soft dependency as the hotel API isn't strictly required for flight search but provides useful input for a common user workflow.",
    "jsonpath": "$.avDates[*].date",
    "dependency_relationship": "Soft Dependency"
}}

#EXAMPLE2:
Target API Documentation:
{{
        "name": "Search_Hotels",
        "endpoint": "/api/v1/hotels/searchHotels",
        "func_description": "Search Hotels. ",
        "parameters": {{
            "type": "object",
            "properties": {{
                "dest_id": {{
                    "type": "Number",
                    "description": "dest_id can be retrieved from api/v1/hotels/searchDestination(Search Hotel Destination) endpoint in Hotels collection.",
                    "example_value": "-2092174",
                    "required": true
                }},
                "search_type": {{
                    "type": "String",
                    "description": "search_type can be retrieved from api/v1/hotels/searchDestination(Search Hotel Destination) endpoint in Hotels collection.",
                    "example_value": "CITY",
                    "required": true
                }},
                "arrival_date": {{
                    "type": "Date (yyyy-mm-dd)",
                    "description": "The date on which you will arrive or check-in",
                    "example_value": "",
                    "required": true
                }},
                "departure_date": {{
                    "type": "Date (yyyy-mm-dd)",
                    "description": "The date of departure or check-out.",
                    "example_value": "",
                    "required": true
                }}
            }}
        }}
}}
Target Parameters Of Target API:
"arrival_date": {{
    "type": "Date (yyyy-mm-dd)",
    "description": "The date on which you will arrive or check-in",
    "example_value": "",
    "required": true
}},
Dict of A Source API Resopnse Field:
{{
    "from_api": "Get_Hotel_Reviews(Tips)", 
    "api_desc": "This API is useful for travelers researching hotel stays and for hotel management to gather feedback. It retrieves guest reviews for a specific hotel, allowing sorting by relevance, date, or proximity score. The response includes detailed reviews with ratings, traveler types, stay details, and hotel responses, helping users assess the overall guest experience. The hotel ID must be obtained from the SearchHotels API.",
    'example_value': [{{'$.result[*].stayed_room_info.checkin': '2025-05-08'}}, {{'$.result[*].stayed_room_info.checkin': '2025-03-17'}}, {{'$.result[*].stayed_room_info.checkin': '2025-02-14'}}]
}}
OUTPUT:
{{
    "reason": "Upon closer examination, there is no meaningful business relationship between historical check-in dates from hotel reviews and the arrival_date parameter for searching hotels. The review check-in dates represent past stays and have no logical connection to future booking dates. The data types may match (yyyy-mm-dd), but this is coincidental rather than representing any actual dependency.",
    "jsonpath": null,
    "dependency_relationship": null
}}

#OUTPUT JSON FORMAT:
{{
    "reason": <<reason>>,
    "jsonpath": <<jsonpath>> or null,
    "dependency_relationship": Soft Dependency or Hard Dependency or null,
}}
Note:The reason should be analyzed from the three perspectives of the rules. Only if all three rules are satisfied should the jsonpath be provided.
"""
        user = f"""
Target API Documentation:
{target_api_info}
Target Parameters Of Target API:
{target_api_params}
Dict of A Source API Resopnse Field:
{api_response_fields}
OUTPUT:
"""
        messages = [
            {"role": "system","content": system},
            {"role": "user","content":  user},
        ]
        
        return messages
    
    def response_filter_fine_grained2(self,target_api_info, target_api_params, source_api_info, Fine_Grained2_Example, api_response_fields_list):
        system = f"""
#ROLE:
You are a professional API Dependency Evaluator. Your task is to analyze whether response fields from source APIs can serve as valid input parameters for a target API.

#INPUT:
1. Target API Documentation
2. Target Parameters Of Target API(One input parameter you need to focus on)
3. Source API Documentation
4. List of most likely Source API Resopnse Fields

#RULES:
1. Carefully read the target API documentation to clearly understand the input parameter requirements of the target API, especially the parameter being focused on.
2. Analyze the response fields of the source API to determine whether there is a business association with the target API parameter(Soft Dependence) or If it is a necessary prerequisite for calling the target API(Hard Dependence).The departure time of the flight is often related to the car rental drop-off time, while the arrival time of the flight is typically associated with the car rental pick-up time.
3. Based on the context of the source API's response example, determine which specific field of the source API can be used as input for the target parameters of target api.
4. Pay attention to whether the data type of the API's response field matches the data type of the target API's parameter.However, sometimes even though the data types do not match exactly, the response field of the source API may contain the information required by the target API parameter. For example, a field with the format "yyy-mm-dd Hh-Mm" may include the value needed for the pickUpTime parameter (which expects the format "24-Hour Hh:Mm"). In such cases, it is important to carefully examine the example values from the response fields to determine if they can be appropriately adapted or extracted for use as input parameters.

#OUTPUT:
1. Provide a confidence score between 0-100 for each judgment. If the confidence is below 80, set the dependency relationship to null.
2. Provide reasons. The reasons should first analyze the meanings of the fields and parameters, determine whether the types match, and consider whether there are reasonable scenarios where the output field of the source API could serve as the input parameter of the target API, paying attention to the causal sequence. If no, reasons are given.


#Example:
{Fine_Grained2_Example}

#OUTPUT JSON FORMAT:
[
    {{
        "target_api_params": <<target_api_params_name>>,
        "reason": <<reason>>,
        "source_jsonpath": <<jsonpath>>,
        "confidence": <<0-100>>,
        "dependency_relationship": <<Soft Dependency(Business-association) or Hard Dependency(Prerequisite API) or null>>,
    }}
]

"""
        user = f"""
Target API Documentation:
{target_api_info}
Target Parameters Of Target API:
{target_api_params}
Source API Documentation:
{source_api_info}
List of most likely Source API Resopnse Fields:
{api_response_fields_list}
OUTPUT:
"""
        messages = [
                {"role": "system","content": system},
                {"role": "user","content":  user},
            ]
            
        return messages


Fine_Grained2_Example = """
Example1:
Target API Documentation:
{
"name": "Car_Search",
"func_description": "This API is ideal for travelers seeking car rentals at specific locations and times. It searches available vehicles based on pickup/drop-off details, with options to filter by car type, supplier, transmission, and amenities like air conditioning. Users receive detailed rental info including pricing, capacity, features, and supplier ratings. Results can be sorted by recommendation or price, aiding in cost-effective travel planning.",
"parameters": {
    "type": "object",
    "properties": {
        "pickUpId": {
            "type": "String",
            "description": "Pick-up location\nRequired: true\npickUpId can be retrieved from /car/auto-complete endpoint(data->id)\n",
            "example_value": "eyJsYXRpdHVkZSI6IjQwLjc1OTU5IiwibG9uZ2l0dWRlIjoiLTczLjk4NDkxIn0=",
            "required": true
        },
        "pickUpDate": {
            "type": "Date (yyyy-mm-dd)",
            "description": "Pick-up date\nRequired: true\nFormat: YYYY-MM-DD\nEx: 2024-01-25",
            "example_value": "",
            "required": true
        },
        "pickUpTime": {
            "type": "Time (24-Hour Hh:Mm)",
            "description": "Pick-up time\nRequired: true\nFormat: HH:MM\nEx: 10:00",
            "example_value": "",
            "required": true
        },
        "dropOffDate": {
            "type": "Date (yyyy-mm-dd)",
            "description": "Drop-off date\nRequired: true\nFormat: YYYY-MM-DD\nEx: 2024-01-26",
            "example_value": "",
            "required": true
        },
        "dropOffTime": {
            "type": "Time (24-Hour Hh:Mm)",
            "description": "Drop-off time\nRequired: true\nFormat: HH:MM\nEx: 10:00",
            "example_value": "",
            "required": true
        },
    },
    "required": [
        "pickUpId",
        "pickUpDate",
        "pickUpTime",
        "dropOffDate",
        "dropOffTime"
    ]
}
Target Parameters Of Target API:
"pickUpTime": {
    "type": "Time (24-Hour Hh:Mm)",
    "description": "Pick-up time\nRequired: true\nFormat: HH:MM\nEx: 10:00",
    "example_value": "",
    "required": true
},
Source API Documentation:
{
    "name": "Search_Flights",
    "endpoint": "/api/v1/flights/searchFlights",
    "func_description": " ",
    "parameters": {
        "type": "object",
        "properties": {
            "fromId": {
                "type": "String",
                "description": "From/Departure location Id. fromId can be retrieved from api/v1/flights/searchDestination(Search Flight Location) endpoint in Flights collection as id.",
                "example_value": "BOM.AIRPORT",
                "required": true
            },
            "toId": {
                "type": "String",
                "description": "To/Arrival location Id. toId can be retrieved from api/v1/flights/searchDestination(Search Flight Location) endpoint in Flights collection as id.",
                "example_value": "DEL.AIRPORT",
                "required": true
            },
            "departDate": {
                "type": "Date (yyyy-mm-dd)",
                "description": "Departure or travel date.\nFormat: YYYY-MM-DD",
                "example_value": "",
                "required": true
            }
        },
        "required": [
            "fromId",
            "toId",
            "departDate"
        ]
    }
}
List of A Source API Resopnse Field:
[
    {
        "field_name": "$.aggregation.flightTimes[].departure[]",
        "field_example": "[
            {
                "start": "00:00",
                "end": "05:59",
                "count": 31
            },
            {
                "start": "06:00",
                "end": "11:59",
                "count": 61
            },
            {
                "start": "12:00",
                "end": "17:59",
                "count": 54
            }
        ]
    },
    {
        "field_name": "$.flightOffers[].segments[].legs[]",
        "field_example": "[
            {
                "departureTime": "2025-06-15T06:00:00",
                "arrivalTime": "2025-06-15T07:55:00",
                "legs": [
                    {
                        "departureTime": "2025-06-15T06:00:00",
                        "arrivalTime": "2025-06-15T07:55:00",
                        "departureAirport": {
                            "type": "AIRPORT",
                            "code": "BOM",
                            "name": "Chhatrapati Shivaji International Airport Mumbai",
                            "city": "BOM",
                            "cityName": "Mumbai",
                            "country": "IN",
                            "countryName": "India",
                            "province": "Maharashtra"
                        },
                        "arrivalAirport": {
                            "type": "AIRPORT",
                            "code": "DEL",
                            "name": "Delhi International Airport",
                            "city": "DEL",
                            "cityName": "New Delhi",
                            "country": "IN",
                            "countryName": "India"
                        },
                    }
                ]
            }
        ]" 
    }
    
]
Output:
[
    {
        "reason": "The 'pickUpTime' parameter in the target API requires a specific car rental return time (24-hour format). The source API's 'arrivalTime' field in flight segments provides exact arrival timestamps (e.g., '2025-06-15T07:55:00'). While the data types differ (timestamp vs time), the time portion can be extracted. This creates a potential business association where a traveler wants to rent a car two hours after the flight arrives.,
        "jsonpath": "$.flightOffers[].segments[].legs[].arrivalTime",
        "confidence": 90,
        "dependency_relationship": "Soft Dependency(Business-association)"
    },
    {
        "reason": "The 'departure[]' time ranges represent when flights take off, which is irrelevant for determining car rental drop-off times. Even if considering a scenario where someone rents a car before departure (which contradicts the target API's purpose), these are still aggregated ranges rather than specific flight times.",
        "jsonpath": "$.aggregation.flightTimes[].departure[]",
        "confidence": 10,
        "dependency_relationship": null
    }
]
"""






if __name__ == '__main__':
    # Target API Documentation:
# {target_api_info}
# Target Parameters Of Target API:
# {target_api_params}
# Dict of an API Resopnse Field:
# {api_response_fields}
    c = ApiLinkPrompts()
    print(c.response_filter_one())