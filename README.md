# GraphLink
GraphLink文件夹主要是构建图的暂时可以不用看，处理结果存到了Tool版本1 和 Tool(1)版本2里
1. Tool版本1 是根据complexbeanch文档进行处理的，当时处理流程有些问题。加上自己当时并不想用complexbeanch的静态请求，但是本身car类别的api在网站上挂掉了因此做了tool版本2。 直接查看ApiInfo_update(1)文件夹即可。
2. Tool版本2 改进了代码 并将car类型的api进行替换 从rapidapi上找到相似的car_api,爬取的文档进行构建。因此Tool1版本和Tool2版本car_api文档不相同。直接查看required_params_link(4)即可。

# GraphPalnner
GraphPlanner文件夹是利用图做推理的
