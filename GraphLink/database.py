'''
参数和响应描述字段数据库建立
'''
import os
import sys
import dotenv
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from tool import ApiInfo
from typing import Union, Dict
from logger import Logger
import logging
import glob
from basellms import DeepSeekRequest, QwenRequest, OpenAIEmbeddingRequest,LocalEmbeddingRequest
from pymilvus import MilvusClient, DataType
from typing import List, Dict, Union, Any, Iterator, Optional
from utils.utilize import *
import numpy as np

dotenv.load_dotenv("/home/snrobot/lin/GraphLinkTools/.env")

class APIDocEmbedder:
    def __init__(self,
        milvus_uri: str = "/home/snrobot/lin/GraphLinkTools/database/params_response_openai.db",
        milvus_token: str = "root:Milvus",
        collection_name: str = "api_docs",
        embed_model_name: str = "text-embedding-3-small",  # 轻量级嵌入模型
        gpt_base_url:str = "https://api.openai.com/v1",
        dimension: int = 1536  # 模型维度):
    ):
        self.client = MilvusClient(uri=milvus_uri)
        self.collection_name = collection_name
        self.dimension = dimension
        if gpt_base_url is not None:
            self.embedder = OpenAIEmbeddingRequest(
                model_name=embed_model_name,
                api_key=os.getenv("OPENAI_API_KEY"),
                base_url=gpt_base_url
            )
        else:
            self.embedder = LocalEmbeddingRequest(
                model_name=embed_model_name,)
        
        # self.delete_collection()
        self._setup_collection()  
    def delete_collection(self):
        if self.client.has_collection(self.collection_name):
            self.client.drop_collection(self.collection_name)
            print("集合已删除")
    def _setup_collection(self):
        """创建集合（如果不存在）"""
        if not self.client.has_collection(self.collection_name):
            schema = MilvusClient.create_schema()
            schema.add_field(field_name="id",datatype=DataType.INT64,is_primary=True,auto_id=True,)
            schema.add_field(field_name="type",datatype=DataType.VARCHAR, max_length=20)
            schema.add_field(field_name="path_name",datatype=DataType.VARCHAR, max_length=50)
            schema.add_field(field_name="api_name",datatype=DataType.VARCHAR, max_length=50)
            schema.add_field(field_name="native_name",datatype=DataType.VARCHAR, max_length=50)
            schema.add_field(field_name="desc",datatype=DataType.VARCHAR, max_length=200)
            schema.add_field(field_name="desc_embed",datatype=DataType.FLOAT_VECTOR, dim=self.dimension)
            
            index_params = self.client.prepare_index_params()
            index_params.add_index(
                field_name="desc_embed", 
                index_type="AUTOINDEX",
                metric_type="COSINE"
            )
            
            self.client.create_collection(collection_name=self.collection_name, schema=schema, index_params=index_params)
            print(f"集合 {self.collection_name} 创建成功")
        res = self.client.get_load_state(collection_name=self.collection_name)
        print(f"集合 {self.collection_name} 加载状态: {res}")
        
    def prepare_data(self, api_folder_path):
        file_paths = glob.glob(os.path.join(api_folder_path, '*.json'))
        for i, file_path in enumerate(tqdm(file_paths, desc="Processing API files",total=len(file_paths))):
            # if i < 15: continue
            notebook = ApiInfo(**json.load(open(file_path)))
            api_name = notebook.name
            print(f"Processing {api_name}...")
            response_desc_list = notebook.response_desc_list
            
            #<---------- 插入响应------------->
            if response_desc_list not in ("", [], {}, None):
                #获取嵌入
                res_strlist = []
                for i, res in enumerate(response_desc_list):
                    desc = f"{res['name']}:{res['description']}"
                    res_strlist.append(desc)
                
                res_embeddings = self.embedder.get_embedding(res_strlist)
                res_embeddings = np.array(res_embeddings, dtype=np.float32)
                
                #存入数据库里
                data1 = []
                for i, res in enumerate(response_desc_list):
                    data1.append({
                        "type": "response",
                        "path_name": res["path_name"],
                        "api_name":api_name,
                        "native_name": res["name"],
                        "desc":res["description"],
                        "desc_embed":res_embeddings[i]
                    })
                self.insert(data1)
            #<---------- 插入参数------------->
            if notebook.enhance_params_desc["enhanced_parameters"] not in ("", [], {}):
                param_strlist = []
                for i, (name, value) in enumerate(notebook.enhance_params_desc["enhanced_parameters"].items()):
                    desc = f"{name}:{value}"
                    param_strlist.append(desc)
                
                params_embeddings = self.embedder.get_embedding(param_strlist)
                params_embeddings = np.array(params_embeddings, dtype=np.float32)
                
                data2 = []
                for i, (name, value) in enumerate(notebook.enhance_params_desc["enhanced_parameters"].items()):
                    data2.append({
                        "type": "params",
                        "path_name": "",
                        "api_name":api_name,
                        "native_name": name,
                        "desc":value,
                        "desc_embed":params_embeddings[i]
                    })
                self.insert(data2)
            print(f"Finished processing {api_name}.")   
                
    def insert(self, data):
        self.client.insert(collection_name=self.collection_name, data=data)
        
    # 直接返回结果 不带任何过滤条件的
    def search_by_vector(self, query_vector, topk=10):
        res = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=topk,
            output_fields=["id", "type", "path_name", "api_name", "native_name", "desc", "desc_embed"]
        )
        
        return res
    
    #返回一个api的所有参数和响应
    def query_by_api(self, api_name):
        res = self.client.query(
            collection_name=self.collection_name,
            filter=f"api_name == '{api_name}'",
            output_fields=["id", "type", "path_name", "api_name", "native_name", "desc", "desc_embed"]
        )
        #对结果进行分类
        res_class = {"params":[], "response":[]}
        for item in res:
            if item["type"] == "params":
                res_class["params"].append(item)
            else:
                res_class["response"].append(item)
        return res_class
    #根据响应搜索参数
    def search_api_params(self, query_vector, topk=10):
        pass
    #根据一个api的参数搜索响应
    def search_api_response(self, api_name:None, query_vector:List, topk=10, ):
        if api_name is not None:
            filter_params = f"type == 'response' and api_name != '{api_name}'"
        else:
            filter_params = f"type == 'response'"
            
        res = self.client.search(
            collection_name=self.collection_name,
            data=query_vector,
            filter=filter_params,
            limit=topk,
            output_fields=["id", "type", "path_name", "api_name", "native_name", "desc", "desc_embed"]
        )
        
        return res
    
if __name__ == "__main__":
    apiembeder = APIDocEmbedder(
        collection_name="all_minv3",
        embed_model_name="/home/snrobot/lin/GraphLinkTools/sentence_similiary/all-MiniLM-L6-v2",
        gpt_base_url=None,
        dimension=384,
        
    )
    api_folder_path = "/home/snrobot/lin/GraphLinkTools/Tools(1)/ApiInfo_update"
    apiembeder.prepare_data(api_folder_path)
    
    
    # res = apiembeder.query_by_api("Get_Filter")
    # for item in res["params"]:
    #     print(item["native_name"] + ": " + item["desc"])
    # print(type(res["params"][0]["desc_embed"]))
    # res1 = apiembeder.search_api_response(api_name=None, query_vector= [res["params"][7]["desc_embed"]], topk=20)
    # for item in res1[0]:
    #     print(item["api_name"] + " " + item["path_name"] + ": " + item["desc"])
    
