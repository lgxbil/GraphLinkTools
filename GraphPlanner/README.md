# 说明文档
## 运行evaluation文件，
流程：
1. 通过GraphAct_1.py构建流程图
2. 将1步的流程图输入给action.py进行求解（目前action是code方式。日后action.py 可以换成多种求解方式验证流程图的有效性）
## 其他文件说明
1. LLM文件是调用大模型接口文件
2. prompt1.py（主要构建流程图和code提示词） 和 prompt_code是提示词文件
3. utils_planner.py是配合GraphAct_1.py的一些处理函数 （无关）
4. 其他文件都是上个版本的代码或者提示词 （无关）
   
# 文件夹说明
1. result是评估结果文件
2. data中APIinfo_update(3)是目前使用的文档说明
3. 目前使用的工具关系图文档是在GraphLinkTools/gound_truth文件夹里的api_link_gt_clean(3).jsonl

   
