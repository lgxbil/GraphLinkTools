import copy
import json
from typing import List, Dict, Union, Any, Iterator, Optional
from dataclasses import dataclass, asdict

@dataclass
class ApiInfo:
    name: str
    docstring: str
    instance: Optional[List] = None
    #
    category: Optional[str] = None
    tool: Optional[str] = None
    api_idx: Optional[str] = None
    params:Optional[Dict] = None
    response: Optional[Union[Dict, List]] = None
    # 未来相似度计算
    enhance_func_desc = Optional[str] = None
    params_desc = Optional[List[Dict]] = None
    response_desc = Optional[List[Dict]] = None
    
    depends_on = Optional[List] = None
    verified: bool = False
    
    def to_dict(self):
        return asdict(self)