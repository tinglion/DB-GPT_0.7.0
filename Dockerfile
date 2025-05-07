FROM eosphorosai/dbgpt-openai:v0.7.0

# 设置环境变量
ENV TZ=Asia/Shanghai
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# 安装 uv
RUN apt-get update && apt-get install -y curl vim
RUN pip install uv

WORKDIR /app
COPY . .

# 安装 依赖 --extra "proxy_ollama"
RUN uv sync --all-packages --extra "base" --extra "proxy_openai" --extra "rag" --extra "storage_chromadb" --extra "dbgpts"

# 确保二进制在 PATH 中
ENV PATH="/root/.local/bin:${PATH}"

# 设置生产环境
ENV NODE_ENV=production

# 运行命令
# CMD ["uv", "run", "dbgpt", "start", "webserver", "--config", "/app/configs/dbgpt-proxy-openai-mysql.toml"]
