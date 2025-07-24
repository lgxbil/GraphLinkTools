import time
from openai import OpenAI
from typing import Union,List
import dotenv
import os
from sentence_transformers import SentenceTransformer
import numpy as np
dotenv.load_dotenv("/home/snrobot/lin/GraphLinkTools/.env")

class BaseRequest:
    def __init__(self, model_name):
        self.model_name = model_name
        self.usage = []
        self.client = OpenAI(api_key='', base_url='')

    def generate(self,
                 messages=None,
                 stop=None,
                 max_len=1000,
                 temp=1,
                 n=1,
                 **kwargs):
        ...
    def __call__(self, *args, **kwargs):
        ...


class DeepSeekRequest(BaseRequest):
    def __init__(self, model_name, api_key, base_url):
        super().__init__(model_name)
        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model_name
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def __call__(
            self,
            messages=None,
            stop=None,
            max_tokens=8192,
            min_tokens=16,
            temp=0.7,
            top_p=0.95,
            n=1,
            **kwargs
    ):
        payload = {
            "model": self.model_name,
            "messages": messages,
            'max_tokens': max_tokens,
            "temperature": temp,
            "n": n, 
            # 'stop': stop,
            "top_p": top_p,
        }
        # deepseek的json是response_format={'type': 'json_object'}
        payload.update(kwargs)
        
        # print(payload)

        for i in range(10):
            try:
                begin = time.time()
                response = self.client.chat.completions.create(**payload)
                end = time.time()
                cost = end - begin
                
                # 处理响应内容
                content = response.choices[0].message.content if n == 1 else [res.message.content for res in response.choices]
                
                results = {
                    "content": content,
                    "time": cost,
                    "usage": [response.usage.completion_tokens, 
                             response.usage.prompt_tokens, 
                             response.usage.total_tokens]
                }
                return results
            except Exception as e:
                print(f"API error (attempt {i+1}/10):", str(e))
                time.sleep(30)
        
        return {
            "content": 'no response from DeepSeek model...', 
            "time": -1, 
            "usage": [0, 0, 0]
        }

class QwenRequest(BaseRequest):
    def __init__(self, model_name, api_key, base_url):
        super().__init__(model_name)
        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model_name
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def __call__(
            self,
            messages=None,
            stop=None,
            max_tokens=8192,
            min_tokens=16,
            temp=0.9,
            top_p=0.95,
            n=1,
            **kwargs
    ):
        payload = {
            "model": self.model_name,
            "messages": messages,
            'max_tokens': max_tokens,
            "temperature": temp,
            "n": n, 
            # 'stop': stop,
            "top_p": top_p,
        }
        # deepseek的json是response_format={'type': 'json_object'}
        payload.update(kwargs)
        
        
        
        # print(payload)

        for i in range(10):
            try:
                begin = time.time()
                response = self.client.chat.completions.create(**payload)
                end = time.time()
                cost = end - begin
                
                if "stream" in payload and payload["stream"]:
                    content = ""
                    print("流式输出内容为：")
                    for chunk in response:
                        # 如果stream_options.include_usage为True，则最后一个chunk的choices字段为空列表，需要跳过（可以通过chunk.usage获取 Token 使用量）
                        if chunk.choices:
                            delta = chunk.choices[0].delta
                            if delta.content is not None:
                                content += delta.content
                else:
                # 处理响应内容
                    content = response.choices[0].message.content if n == 1 else [res.message.content for res in response.choices]
                    
                results = {
                    "content": content,
                    "time": cost,
                    # "usage": [response.usage.completion_tokens, 
                    #         response.usage.prompt_tokens, 
                    #         response.usage.total_tokens]
                }
                return results
            except Exception as e:
                print(f"API error (attempt {i+1}/10):", str(e))
                time.sleep(30)
        
        return {
            "content": 'no response from DeepSeek model...', 
            "time": -1, 
            "usage": [0, 0, 0]
        }
    
class QwenDeepSeekRequest(BaseRequest):
    def __init__(self, model_name, api_key, base_url):
        super().__init__(model_name)
        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model_name
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def __call__(
            self,
            messages=None,
            stop=None,
            max_tokens=8192,
            min_tokens=16,
            temp=0.9,
            top_p=0.95,
            n=1,
            **kwargs
    ):
        payload = {
            "model": self.model_name,
            "messages": messages,
            'max_tokens': max_tokens,
            "temperature": temp,
            "n": n, 
            # 'stop': stop,
            "top_p": top_p,
        }
        # deepseek的json是response_format={'type': 'json_object'}
        payload.update(kwargs)
        
        # print(payload)

        for i in range(10):
            try:
                begin = time.time()
                response = self.client.chat.completions.create(**payload)
                end = time.time()
                cost = end - begin
                
                # 处理响应内容
                content = response.choices[0].message.content if n == 1 else [res.message.content for res in response.choices]
                
                results = {
                    "content": content,
                    "time": cost,
                    "usage": [response.usage.completion_tokens, 
                             response.usage.prompt_tokens, 
                             response.usage.total_tokens]
                }
                return results
            except Exception as e:
                print(f"API error (attempt {i+1}/10):", str(e))
                time.sleep(30)
        
        return {
            "content": 'no response from DeepSeek model...', 
            "time": -1, 
            "usage": [0, 0, 0]
        }


class OpenAIRequest:
    pass

class OpenAIEmbeddingRequest:
    def __init__(self, model_name, api_key, base_url):
        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model_name
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        
    def get_embedding(self, text:List) -> List:
        response = self.client.embeddings.create(
            input=text,
            model=self.model_name
        )
        return [item.embedding for item in response.data]

class LocalEmbeddingRequest:
    def __init__(self, model_name):
        self.model_name = model_name 
        self.model = SentenceTransformer(self.model_name)
    def get_embedding(self, text:List[str]) -> List:
        embeddings = self.model.encode(text)
        return embeddings.tolist() if isinstance(embeddings, np.ndarray) else embeddings
    
 
if __name__ == '__main__':
    params = {
        "model_name": "deepseek-chat",
        "api_key": "sk-f17e647c3ba449e29415f1f64c070ae6",
        "base_url": "https://api.deepseek.com"
    }
    gpt = DeepSeekRequest(**params)
    strc = """
You are a professional API Dependency Evaluator. Your task is to analyze whether response fields from source APIs can serve as valid input parameters for a target API, return the top 10 most relevant results. Based on:
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
Target API Documentation:
"docs_row": {
        "name": "Search_Hotels",
        "endpoint": "/api/v1/hotels/searchHotels",
        "func_description": "Search Hotels. ",
        "parameters": {
            "type": "object",
            "properties": {
                "dest_id": {
                    "type": "Number",
                    "description": "dest_id can be retrieved from api/v1/hotels/searchDestination(Search Hotel Destination) endpoint in Hotels collection.",
                    "example_value": "-2092174",
                    "required": true
                },
                "search_type": {
                    "type": "String",
                    "description": "search_type can be retrieved from api/v1/hotels/searchDestination(Search Hotel Destination) endpoint in Hotels collection.",
                    "example_value": "CITY",
                    "required": true
                },
                "arrival_date": {
                    "type": "Date (yyyy-mm-dd)",
                    "description": "The date on which you will arrive or check-in",
                    "example_value": "",
                    "required": true
                },
                "departure_date": {
                    "type": "Date (yyyy-mm-dd)",
                    "description": "The date of departure or check-out.",
                    "example_value": "",
                    "required": true
                },
                "adults": {
                    "type": "Number",
                    "description": "The number of guests who are 18 years of age or older. The default value is set to 1.",
                    "example_value": "1",
                    "required": false
                },
                "children_age": {
                    "type": "String",
                    "description": "The number of children, including infants, who are under 18.\nExample:\nChild 1 Age = 8 months\nChild 2 Age = 1 year\nChild 3 Age = 17 years\nHere is what the request parameter would look like:\nchildren_age: 0,1,17",
                    "example_value": "0,17",
                    "required": false
                },
                "room_qty": {
                    "type": "Number",
                    "description": "The number of rooms that are required. The default value is set to 1.",
                    "example_value": "1",
                    "required": false
                },
                "page_number": {
                    "type": "Number",
                    "description": "The page number.",
                    "example_value": "1",
                    "required": false
                },
                "price_min": {
                    "type": "Number",
                    "description": "Minimum Price filter for search.",
                    "example_value": "",
                    "required": false
                },
                "price_max": {
                    "type": "Number",
                    "description": "Maximum Price filter for search.",
                    "example_value": "",
                    "required": false
                },
                "sort_by": {
                    "type": "String",
                    "description": "sort_by can be retrieved from api/v1/hotels/getSortBy(Get Sort By) endpoint in Hotels collection.",
                    "example_value": "",
                    "required": false
                },
                "categories_filter": {
                    "type": "String",
                    "description": "categories_filter can be retrieved from api/v1/hotels/getFilter(Get Filter) endpoint in Hotels collection.",
                    "example_value": "",
                    "required": false
                },
                "units": {
                    "type": "Enum",
                    "description": "The measurement of distance in metric or imperial.",
                    "example_value": "",
                    "required": false
                },
                "temperature_unit": {
                    "type": "Enum",
                    "description": "The temperature unit in Fahrenheit or Celsius.\nc = Celsius\nf = Fahrenheit",
                    "example_value": "",
                    "required": false
                },
                "languagecode": {
                    "type": "String",
                    "description": "To obtain the response data in a specific language, enter the languagecode. languagecode can be retrieved from api/v1/meta/getLanguages(Get Languages\n) endpoint in Meta collection.",
                    "example_value": "en-us",
                    "required": false
                },
                "currency_code": {
                    "type": "String",
                    "description": "The currency code. currency_code can be retrieved from api/v1/meta/getCurrency(Get Currency) endpoint in Hotels collection.",
                    "example_value": "AED",
                    "required": false
                },
                "location": {
                    "type": "String",
                    "description": "location can be retrieved from api/v1/meta/getLocations(Get Location) endpoint in Meta collection.",
                    "example_value": "US",
                    "required": false
                }
            },
            "required": [
                "dest_id",
                "search_type",
                "arrival_date",
                "departure_date"
            ]
        }
    },
Target parms:
"dest_id": {
                    "type": "Number",
                    "description": "dest_id can be retrieved from api/v1/hotels/searchDestination(Search Hotel Destination) endpoint in Hotels collection.",
                    "example_value": "-2092174",
                    "required": true
                },
List of Some Source API Fields:
Get_Nearby_Cities $[].dest_id: A unique identifier for the destination (e.g., 20085521).
Search_Hotel_Destination $[].dest_id: A unique identifier for the destination (e.g., '-1456928' for Paris).
Search_Attraction_Location $.destinations[].id: A unique identifier for the destination, encoded in Base64 format.
Car_Search $.search_context.searchId: A unique identifier (UUID) for the search session, used to track or reference this specific search query.
Car_Auto-Complete $[].id: A unique identifier for the location, possibly encoded (e.g., 'eyJsYXRpdHVkZSI6IjQwLjc2ODA3NDAzNTY0NDUiLCJsb25naXR1ZGUiOiItNzMuOTgxODk1NDQ2Nzc3MyJ9').
Search_Taxi $.results[].resultId: A unique identifier for the transportation option (e.g., 'c939cecb-59c2-42e6-a149-05797c761e2e').
Car_Search $.search_results[].route_info.pickup.location_id: Unique identifier for the pickup location (e.g., '41721').
Search_Flights_Multi_Stops $.searchId: A unique identifier for the flight search session (e.g., '99527EA1799731DFBC5DCC0D3A95CE8B').
Search_Flights $.searchId: A unique identifier for the flight search session (e.g., '18AD19EE6C7237C08953DC22C43CB5AE').
Car_Search $.filter[].id: A unique identifier for the filter category (e.g., 'depotLocationType').
Car_Search $.search_results[].route_info.dropoff.location_id: Unique identifier for the dropoff location (e.g., '41721').
Search_Taxi $.journeys[].janusSearchReference: A unique reference identifier for the journey search (e.g., 'ddea7ea5-7456-4e71-b752-14226e0d6e2a').
Search_Attraction_Location $.destinations[].ufi: A unique identifier for the destination.
Car_Search $.filter[].categories[].id: A unique identifier for the category (e.g., 'depotLocationType::DOWNTOWN').
Search_Taxi $.journeys[].pickupLocation.locationId: A unique identifier for the pickup location (e.g., 'ChIJRym9mVDI5zsRrqh0xGAazB4').
Search_Flight_Location $[].id: A unique identifier for the location, combining the code and type (e.g., 'NYC.CITY').
Search_Taxi $.journeys[].dropOffLocation.locationId: A unique identifier for the drop-off location (e.g., 'ChIJ____b8DR5zsRVz_XpIUEKcA').
Location_to_Lat_Long $[].place_id: A unique identifier for the place (e.g., 'ChIJaXQRs6lZwokRY6EFpJnhNNE').
Car_Search $.search_context.recommendationsSearchUniqueId: A unique identifier (UUID) for the recommendations generated from this search, used to retrieve or update the recommendations.
Get_Nearby_Cities $[].dest_type: The type of destination (e.g., 'city').
Get_Room_List $.rooms.7471721.facilities[].id: Unique identifier for the facility.
Get_Room_List $.rooms.7471710.facilities[].id: Unique identifier for the facility.
Get_Room_List $.rooms.7471708.facilities[].id: Unique identifier for the facility.
Search_Attractions $.filterOptions.ufiFilters[].tagname: A unique identifier for the location filter.
Car_Search $.search_results[].vehicle_info.v_id: Unique identifier for the vehicle (e.g., '695750651').
List_Restaurants_By_Search_Query $.results[].id: The unique identifier for the restaurant on TripAdvisor.
Get_Hotel_Facilities $.facilities[].id: The unique identifier for the facility.
Get_Room_List $.rooms.7471728.facilities[].id: The unique identifier for the facility.
Get_Room_List $.rooms.7471725.facilities[].id: The unique identifier for the facility.
Car_Auto-Complete $[].location_id: An identifier for the location. Null in the provided examples.
Search_Hotels $.hotels[].property.ufi: A unique identifier for the location.
Search_Attractions $.products[].ufiDetails.ufi: A unique identifier for the location.
Search_Hotels_By_Coordinates $.result[]: An object representing a hotel search result.
Search_Hotel_Destination $[].dest_type: The type of destination (e.g., 'city', 'district', 'landmark').
Search_Flights $.flightOffers[].unifiedPriceBreakdown.items[].id: A unique identifier for the item (e.g., 'flight_adult').
Search_Flights_Multi_Stops $.flightOffers[].unifiedPriceBreakdown.items[].id: A unique identifier for the item (e.g., 'flight_adult').
Search_Attraction_Location $.destinations[].__typename: The type of the destination suggestion (e.g., 'AttractionsSearchDestinationSuggestion').
Search_Flights $.flightOffers[].unifiedPriceBreakdown.items[].items[].id: A unique identifier for the sub-item (e.g., 'flight_adult-basefare').
Search_Flights_Multi_Stops $.flightOffers[].unifiedPriceBreakdown.items[].items[].id: A unique identifier for the sub-item (e.g., 'flight_adult-basefare').
Car_Search $.search_results[].route_info.pickup.location_hash: Hash representing the pickup location.
Search_Restaurants $[].id: A unique identifier for the location or establishment (e.g., 60763 for New York City).
Search_Attraction_Location $.destinations[]: An object representing a travel destination with activity information.
Get_Room_List $.rooms.7471721.facilities[].facilitytype_id: Unique identifier for the facility type.
Get_Room_List $.rooms.7471708.facilities[].facilitytype_id: Unique identifier for the facility type.
Get_restaurant_details $.id: Unique identifier for the restaurant.
Get_Sort_By $[].id: The unique identifier for the sorting option (e.g., 'upsort_bh', 'popularity', 'distance').
Car_Search $.content.map.supplierLocations[].metaData.locationHash: A hash representing the location (e.g., 'Sm9obiBGIEtlbm5lZHkgSW50ZXJuYXRpb25hbCBBaXJwb3J0').
Search_Attraction_Location $.products[].id: A unique identifier for the product, encoded in Base64 format.
Car_Search $.search_key: A base64-encoded search key containing parameters such as driver's age, pickup and drop-off dates and times, location coordinates, rental duration, and service features.
Get_Hotel_Photos $[].id: The unique identifier for the hotel image (e.g., 613758026).
Search_Flights $.flightOffers[].includedProductsBySegment[][].travellerReference: A unique identifier for the traveler (e.g., '1').
Search_Flights_Multi_Stops $.flightOffers[].includedProductsBySegment[][].travellerReference: A unique identifier for the traveler (e.g., '1').
Search_Hotels_By_Coordinates $.result[].id: The unique identifier for the property card (e.g., 'property_card_11361227').
Search_Hotels $.hotels[].property.id: The unique identifier for the hotel property.
Property_Children_Policies $.trackedExperiments[].id: The unique identifier for the experiment (e.g., '2269860').
Get_Room_List $.rooms.7471725.facilities[].facilitytype_id: The unique identifier for the facility type.
Get_Room_List $.rooms.7471728.facilities[].facilitytype_id: The unique identifier for the type of facility.
Car_Search $.search_results[].accessibility.pick_up_location: Pickup location description (e.g., 'Pick-up information: Shuttle Bus').
Get_Hotel_Reviews_Filter_Metadata $.hotel_id: The unique identifier for the hotel (e.g., '1377073').
Search_Taxi $.results[].legPriceBreakdown[].supplierLocationId: The unique identifier for the supplier's location (e.g., 6189).
Search_Hotel_Destination $[].city_ufi: The unique identifier for the city, if applicable (null if not applicable).
Get_Question_And_Answer $.q_and_a_pairs[].question_id: The unique identifier for the question.
Get_Min_Price_Multi_Stops $[].accuracyTrackerId: A unique identifier used for tracking the accuracy of the flight search results.
Get_Popular_Attraction_Near_By $.closest_landmarks[]: An object representing a landmark with its details.
Taxi_Search_Location $[].googlePlaceId: The unique identifier for the hotel on Google Maps (e.g., 'ChIJDwzsBVRYwokRvSHYftloJ1I').
Property_Children_Policies $.trackedExperiments[].uviType: The type of unique visitor identifier (e.g., 'device_id').
Search_Attractions $.products[].id: A unique identifier for the product.
Get_Room_List $.hotel_id: The unique identifier for the hotel property.
Search_Hotels_By_Coordinates $.result[].hotel_id: The unique identifier for the hotel (e.g., 11361227).
Get_Hotel_Review_Scores $[].hotel_id: The unique identifier for the hotel (e.g., 5955189).

    """
    messages = [
        {
            "role": "user",
            "content": strc
        }
    ]
    out_ = gpt(messages=messages)
    print(out_)
    
    # params = {
    #     "model_name": "qwen3-235b-a22b",
    #     "api_key": "sk-f418d022aa7846eda995a61fef80bf85",
    #     "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"
    # }
    # gpt = QwenRequest(**params)
    # messages = [
    #     {
    #         "role": "user",
    #         "content": "What is the capital of France?"
    #     }
    # ]
    # out_ = gpt(messages=messages, stream=True, extra_body={"enable_thinking": False})
    # print(out_)
    
    # params = {
    #     "model_name": "deepseek-v3",
    #     "api_key": "sk-f418d022aa7846eda995a61fef80bf85",
    #     "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"
    # }
    # gpt = QwenDeepSeekRequest(**params)
    # messages = [
    #     {
    #         "role": "user",
    #         "content": "What is the capital of France?"
    #     }
    # ]
    # out_ = gpt(messages=messages)
    # print(out_)
    
  