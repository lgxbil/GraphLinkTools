import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.utilize import *
from typing import Union, Dict,List
from logger import Logger

import logging
from jsonpath_ng import jsonpath, parse
import json
import dotenv

import random
import copy
import glob,pickle
dotenv.load_dotenv("/home/snrobot/lin/GraphLinkTools/.env")


def jsonpath_clean(api_folder_path, output_folder):
    info_files = glob.glob(os.path.join(api_folder_path, '*.json'))
    notebooks = {}
    for i, file_path in enumerate(info_files):
        notebook = ApiInfo(**json.load(open(file_path)))
        notebooks[notebook.name] = notebook
        
    for i,notebook in tqdm(enumerate(notebooks.values()), total=len(notebooks), desc="Processing APIs"):
        print(f"Processing API {i+1}/{len(notebooks)}: {notebook.name}")
        api_name, api_enchance_doc, api_response_schema = get_api_base_info(notebook)
        
        
        depends_on = notebook.depends_on if notebook.depends_on else []
        depens_on_copy = []

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
            depens_on_copy.append(dependency)

        notebook.update(
                depends_on = depends_on
            )
        #写入到新文件夹里
        save_notebook(
            notebook,
            output_folder,
            notebook.name
        )

#对jsonpath进一步过滤
def rules_filter(self):
    pass


#<-------------------------------------------------------------->
def save_notebook(notebook, output_folder, name):
    os.makedirs(output_folder, exist_ok=True)
    file_path = os.path.join(output_folder, f'{name}.json')
    write_file(notebook.to_dict(), file_path)
    
    print(f"Saved to {file_path}")           
            
            
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

if __name__ == "__main__":
    api_folder_path = "/home/snrobot/lin/GraphLinkTools/Tools(1)/required_params_link(3)"
    output_folder = "/home/snrobot/lin/GraphLinkTools/Tools(1)/required_params_link(4)"

    jsonpath_clean(api_folder_path, output_folder)

    # G = draw_graph()
    # draw_static_api_graph(G)
    # export_graph_to_anychart_json()
    
    # from pyvis.network import Network

    # net = Network()
    # net.add_node("A", label="A")
    # net.add_node("B", label="B")
    # net.add_edge("A", "B")
    # net.show("test_graph.html")

    