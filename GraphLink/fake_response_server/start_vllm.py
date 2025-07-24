import subprocess

model_path = "/home/snrobot/lin/Llm-model/qwen2.5-7b"
model_name = "qwen2.5"
port = 12345
api_key = "sk-123"

cmd = [
    "vllm", "serve",
    model_path,
    "--served-model-name", model_name,
    "--gpu-memory-utilization", "0.6",
    "--port", str(port),
]

# 启动 vLLM 服务（非阻塞）
process = subprocess.Popen(cmd)

print(f"vLLM 服务已启动，监听端口 {port}，模型名称为 {model_name}")
