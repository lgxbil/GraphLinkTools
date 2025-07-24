import copy
import json
from typing import List, Dict, Union, Any, Iterator, Optional
from dataclasses import dataclass, asdict

@dataclass
class ApiInfo:
    name: str
    docs_row: Dict
    instance: Optional[List] = None
    #
    category: Optional[str] = None
    tool: Optional[str] = None
    api_idx: Optional[str] = None
    params:Optional[Dict] = None
    api_response_schema: Optional[Union[Dict, List]] = None
    responses: Optional[Union[Dict, List]] = None
    
    response_summary : Optional[str] = None
    # 改进的功能,参数, 响应描述
    enhance_func_desc : Optional[str] = None
    enhance_params_desc : Optional[Dict] = None
    enhance_resfield_desc : Optional[Union[Dict, List]] = None
    
    # 用于相似度计算、
    params_desc_list : Optional[List[str]] = None
    response_desc_list : Optional[List[str]] = None
    
    #依赖图
    depends_on : Optional[List] = None
    verified: bool = False
    
    
    def update(self, **kwargs):
        """
        :param kwargs:
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def to_dict(self):
        return asdict(self)


#节点

@dataclass(frozen=True)
class APINode:
    name: str
    method: str = "GET"
    url: Optional[str] = None
    description: Optional[str] = None
    type: str = "api"
    params:str=None
    response_schema: str = None

    def to_dict(self):
        return asdict(self)

@dataclass(frozen=True)
class FieldNode:
    name: str
    value: str = None
    type: str = "param"
    reason:str=""
    from_api:str=""

    def to_dict(self):
        return asdict(self)
