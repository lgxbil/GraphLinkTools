import sys
import pickle
import multiprocessing
import json
import os
from tqdm import tqdm
import re

def write_file(data,filename,num_processes=20,default_name='train',indent=4):
    if filename.endswith('.json'):
        json.dump(data,open(filename,'w'),indent=indent)
    elif filename.endswith('.jsonl') :
        with open(filename, 'w') as f:
            for line in data:
                f.write(json.dumps(line) + '\n')
    elif filename.endswith('.txt'):
        with open(filename, 'w') as f:
            for line in data:
                f.write(str(line) + '\n')
    elif filename.endswith('.pkl'):
        pickle.dump(data,open(filename,'w'))
    elif '.' not in filename:
        multi_write_jsonl(data,filename,num_processes=num_processes,default_name=default_name)
    else:
        raise "no suitable function to write data"

def write_jsonl(data,filename,ids=None):
    with open(filename,'w') as f:
        for line in tqdm(data):
            f.write(json.dumps(line)+'\n')
    return ids,len(data)

def multi_write_jsonl(data,folder,num_processes=10,default_name='train'):
    """

    :param filename:
    :param num_processes:
    :return:
    """
    if not os.path.exists(folder):
        os.makedirs(folder)
    length = len(data) // num_processes + 1
    pool=multiprocessing.Pool(processes=num_processes)
    collects=[]
    for ids in range(num_processes):
        filename=os.path.join(folder,f"{default_name}{ids}.jsonl")
        collect = data[ids * length:(ids + 1) * length]
        collects.append(pool.apply_async(write_jsonl,(collect,filename,ids)))

    pool.close()
    pool.join()
    cnt=0
    for i,result in enumerate(collects):
        ids,num=result.get()
        assert ids==i
        cnt+=num
    return cnt

def strip_json_markdown(text):
    if text.startswith("```"):
        text = text.strip("`").strip()
        if text.startswith("json"):
            text = text[len("json"):].strip()
    return text

def observation_shorten(response, i):
    if response == None:
        return response

    if isinstance(response, dict):
        # keys_to_delete = [key for key, value in response.items() if (value in ["", None, {}, []])]
        # for key in keys_to_delete:
        #     response.pop(key)

        for key, value in response.items():
            response[key] = observation_shorten(value, i)
            
    elif isinstance(response, list):
        if len(response) > i:
            response = response[:i]
        response = [observation_shorten(item, i) for item in response]

    return response