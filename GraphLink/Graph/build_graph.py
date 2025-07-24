import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from basellms import DeepSeekRequest, QwenRequest
from build_database import APIDocEmbedder
from queue import Queue
from utils.utilize import *
from tool import ApiInfo, APINode, FieldNode
from typing import Union, Dict,List
from logger import Logger
import networkx as nx


from rapidapi import RapidAPICall
import logging
from jsonpath_ng import jsonpath, parse
import json
import dotenv
import json
import random
import copy
import glob,pickle
dotenv.load_dotenv("/home/snrobot/lin/GraphLinkTools/.env")


def build_api_graph(api_folder_path):
    G = nx.DiGraph()
    
    info_files = glob.glob(os.path.join(api_folder_path, '*.json'))
    notebooks = {}
    for i, file_path in enumerate(info_files):
        notebook = ApiInfo(**json.load(open(file_path)))
        notebooks[notebook.name] = notebook
        
    for i,notebook in tqdm(enumerate(notebooks.values()), total=len(notebooks), desc="Processing APIs"):
        print(f"Processing API {i+1}/{len(notebooks)}: {notebook.name}")
        api_name, api_enchance_doc, api_response_schema = get_api_base_info(notebook)
        
        target_api_node = APINode(
            name=api_name, 
            description=api_enchance_doc["func_description"], 
            type="api",
            params = json.dumps(api_enchance_doc["parameters"]), 
            response_schema = json.dumps(api_response_schema), 
        )
        depends_on = notebook.depends_on if notebook.depends_on else []
        for dependency in depends_on:
            target_api_param = dependency["target_api_params"]
            reason = dependency["reason"]
            source_jsonpath = dependency["source_jsonpath"]
            source_api_name = dependency["source_api"]
            #对jsonpath进行验证：
            if not source_jsonpath:
                continue
            source_jsonpath_value = get_example_jsonpath(notebooks[source_api_name], source_jsonpath, 1)
            if not source_jsonpath_value:
                print(f"Invalid jsonpath: {source_jsonpath} source {source_api_name} in API: {api_name}, skipping...")
                continue
            api_name1, api_enchance_doc1, api_response_schema1 = get_api_base_info(notebooks[source_api_name])
            
            source_api_node = APINode(
                name=source_api_name, 
                description=api_enchance_doc1["func_description"], 
                type="api",
                params = json.dumps(api_enchance_doc1["parameters"]), 
                response_schema = json.dumps(api_response_schema1)
            )
            
            target_api_params_node = FieldNode(
                name = target_api_param,
                value = json.dumps(api_enchance_doc["parameters"]["properties"][target_api_param]),
                type = "params",
            )
            source_api_res_node = FieldNode(
                name = source_jsonpath,
                value = json.dumps(source_jsonpath_value),
                type = "response_field",
                reason = reason
            )
            #添加4个节点和3条边
            G.add_node(target_api_node)
            G.add_node(target_api_params_node)
            G.add_node(source_api_node)
            G.add_node(source_api_res_node)
            
            G.add_edge(source_api_node, source_api_res_node)
            G.add_edge(source_api_res_node, target_api_params_node)
            G.add_edge(target_api_params_node, target_api_node)
            
    
    #保存图
    print("Loaded Nodes:", len(G.nodes()))
    print("Loaded Edges:", len(G.edges()))
    with open("/home/snrobot/lin/GraphLinkTools/GraphLink/Graph/graph_raph_data/api_graph.gpickle", "wb") as f:
        pickle.dump(G, f)
   
    return G      
            
        

def get_api_base_info(notebook):
    api_enchance_doc = get_row_api_info(notebook)
    api_name = notebook.name
    api_response_schema = ""
    try:
        if notebook.responses:
            api_response_schema = observation_shorten(notebook.responses[0]['observation'], 1)
    except Exception as e:
        print(notebook.responses)
    return api_name, api_enchance_doc, api_response_schema

from pyvis.network import Network
import pickle
import pickle
from pyvis.network import Network

def draw_graph():
    # 加载图
    with open("/home/snrobot/lin/GraphLinkTools/GraphLink/Graph/graph_raph_data/api_graph.gpickle", "rb") as f:
        G = pickle.load(f)
    
    # 创建 pyvis 网络图（禁用物理引擎）
    net = Network(notebook=False, directed=True, height="1200px", width="100%")
    net.barnes_hut(spring_length=100, damping=0.9)  # 调整参数以减少动态性

    # 将节点与边加入 pyvis，但只用 name 作为展示文本
    for node in G.nodes:
        if node.type == "api":
            net.add_node(n_id=node.name, label=node.name, color="red", size=200)
        elif node.type == "params":
            net.add_node(n_id=node.name, label=node.name, color="blue", size=200)
        elif node.type == "response_field":
            net.add_node(n_id=node.name, label=node.name, color="blue", size=200)

    for u, v in G.edges:
        net.add_edge(u.name, v.name, color="gray", arrows='to', width=3)
    
    # 展示图
    net.show("api_graph.html")

import pickle
import json

def export_graph_to_anychart_json():
    with open("/home/snrobot/lin/GraphLinkTools/GraphLink/Graph/graph_raph_data/api_graph.gpickle", "rb") as f:
        G = pickle.load(f)

    nodes = []
    edges = []

    # 定义类型 → 颜色映射（可根据实际分类扩展）
    type_color_map = {
        "api": "#d62728",   # 蓝色
        "params": "#ff7f0e",    # 橙色
        "response_field": "#2ca02c",   # 绿色
    }

    for node in G.nodes:
        node_type = node.type  # 没有 type 属性就归为 "Other"
        color = type_color_map.get(node_type, "#999999")
        nodes.append({
            "id": node.name,
            "label": node.name,
            "fill": color
        })

    for u, v in G.edges:
        edges.append({
            "from": u.name,
            "to": v.name,
            "normal": {
                "marker": {
                    "type": "arrow"
                }
            }
        })

    data = {
        "nodes": nodes,
        "edges": edges
    }

    with open("anychart_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)




import matplotlib.pyplot as plt
import networkx as nx

def draw_static_api_graph(G):
    plt.figure(figsize=(16, 12))
    pos = nx.spring_layout(G, k=0.5, iterations=100)  # 自动布局

    # 节点颜色区分不同类型
    color_map = []
    for node in G.nodes:
        if hasattr(node, 'type'):
            if node.type == "api":
                color_map.append('skyblue')
            elif node.type == "params":
                color_map.append('lightgreen')
            elif node.type == "response_field":
                color_map.append('orange')
            else:
                color_map.append('grey')
        else:
            color_map.append('grey')

    # 绘图
    nx.draw_networkx_nodes(G, pos, node_color=color_map, node_size=500)
    nx.draw_networkx_edges(G, pos, edge_color='gray', arrows=True, arrowsize=20)
    nx.draw_networkx_labels(G, pos, labels={node: node.name for node in G.nodes if hasattr(node, "name")}, font_size=10)

    plt.title("API Dependency Graph (Static View)")
    plt.axis("off")
    plt.show()


    

if __name__ == "__main__":
    api_folder_path = "/home/snrobot/lin/GraphLinkTools/Tools(1)/required_params_link(2)"
    build_api_graph(api_folder_path)
    # G = draw_graph()
    # draw_static_api_graph(G)
    # export_graph_to_anychart_json()
    
    # from pyvis.network import Network

    # net = Network()
    # net.add_node("A", label="A")
    # net.add_node("B", label="B")
    # net.add_edge("A", "B")
    # net.show("test_graph.html")

    