# note

* 全局规划：packages/dbgpt-core/src/dbgpt/agent/core/plan/planner_agent.py  
  * 主prompt：packages/dbgpt-core/src/dbgpt/agent/core/profile/base.py
  * 接口位置，透传参数：packages/dbgpt-serve/src/dbgpt_serve/agent/agents/controller.py
* 具体agent位置：packages/dbgpt-core/src/dbgpt/agent/expand/summary_assistant_agent.py
* 前端聊天主页：pages/chat/index.tsx
* 前端图表格式检查：components/chart/autoChart/helpers/index.ts
* ?前端如何触发图片功能？
  * setChartsData(contextObj?.template_name === 'report' ? contextObj?.charts : undefined);

## deploy

* 修改toml配置
* pack.py有重复添加同名&不覆盖的bug

```bash
# --extra "proxy_ollama"
uv sync --all-packages --extra "base" --extra "proxy_openai"  --extra "rag" --extra "storage_chromadb" --extra "dbgpts"

uv run dbgpt start webserver --config configs/dbgpt-proxy-openai-local.toml
# or
# uv run 
.\.venv\Scripts\activate.ps1
python packages/dbgpt-app/src/dbgpt_app/dbgpt_server.py --config configs/dbgpt-proxy-openai-local.toml

npx -y supergateway --stdio "uvx mcp-server-fetch"
# npx @modelcontextprotocol/inspector uvx mcp-server-fetch
```

## docker

```bash
docker build -t my-dbgpt:v0.7.0.a .
docker-compose up -d

docker cp packages/dbgpt-core/src/dbgpt/agent/resource/pack.py dbgpt_webserver:/app/packages/dbgpt-core/src/dbgpt/agent/resource/
docker cp packages/dbgpt-core/src/dbgpt/agent/core/profile/base.py dbgpt_webserver:/app/packages/dbgpt-core/src/dbgpt/agent/core/profile/

curl http://localhost:1234/v1/embeddings  \
    -H "Content-Type: application/json"  \
    -d '{"model":"text-embedding-nomic-embed-text-v1.5", "input":"test"}'
curl -X POST http://106.39.129.42:8190/v1/embeddings \
    -H "Authorization: Bearer putibenwushu" \
    -H "Content-Type: application/json" \
    -d '{"model":"qwen2.5:32b", "input":"test"}'
```

## tool_infos 溯源

* agent manager返回agent列表或者字典: .\packages\dbgpt-core\src\dbgpt\agent\core\agent_manage.py
* planner 直接只用item.desc: .\packages\dbgpt-core\src\dbgpt\agent\core\plan\planner_agent.py
* ToolExpert 的desc包含 {tool_infos} : .\packages\dbgpt-core\src\dbgpt\agent\expand\tool_assistant_agent.py

## test

```shell
curl http://106.39.129.42:8190/v1/models       \
    -H "Authorization: Bearer putibenwushu"

curl -X POST http://106.39.129.42:8190/v1/embeddings \
    -H "Authorization: Bearer putibenwushu"       \
    -H "Content-Type: application/json"      \
    -d '{"model":"qwen2.5:32b", "input":"test"}'

curl -X POST http://106.39.129.42:8190/v1/completions    \
    -H "Authorization: Bearer putibenwushu"     \
    -H "Content-Type: application/json"       \
    -d '{"model":"qwen2.5:32b", "prompt":"hi"}'
```
