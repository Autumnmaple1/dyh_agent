# 大运河人物智能体（首版）

一个不依赖 RAG 的三角色原型。当前支持：

- 苏轼（徐州）、陈瑄（淮安）、张伯行（苏州）
- 文旅推荐模式
- 沉浸式故事模式
- FastAPI 后端与自动生成的 OpenAPI 文档
- Vite + React 单页对话窗口
- token 预算、滚动摘要与近期原文结合的混合记忆
- 故事模式结构化状态记忆
- `demo` 离线演示模型，以及 OpenAI-compatible 模型接口

## 架构原则

每个角色是一份独立的结构化人物卡。每次请求只向模型传入：

1. 当前角色的人物卡；
2. 当前模式规则；
3. 超出预算后生成的早期会话滚动摘要；
4. 故事模式的当前幕次、玩家关键行动和上一轮结果；
5. token 预算内的近期原始消息；
6. 本轮用户输入。

因此首版无需向量数据库，也不会把三个角色的完整资料同时加入提示词。

## 本地运行

### Windows 一键启动

Windows 上可直接双击 [start.bat](start.bat)。脚本会自动检查 Python 环境和 pnpm、构建前端并启动服务，然后打开 <http://127.0.0.1:8010/>。首次运行前需要已安装 Python 3.11+ 与 pnpm。

需要 Python 3.11 或更高版本。

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

打开：

- 对话窗口：<http://127.0.0.1:8000>
- API 文档：<http://127.0.0.1:8000/docs>

默认 `AI_PROVIDER=demo`，无需密钥即可检查完整链路。

## 前端开发

前端源码位于 `frontend/`，开发服务器会把 `/api` 请求代理到 `127.0.0.1:8010`：

```powershell
cd frontend
pnpm install
Copy-Item .env.example .env
pnpm dev
```

地图使用高德 JS API 2.0（GCJ-02 坐标）。请先在 `frontend/.env` 中配置：

```dotenv
VITE_AMAP_KEY=your-amap-web-js-key
VITE_AMAP_SECURITY_CODE=your-amap-security-code
VITE_AMAP_VERSION=2.0
```

生产构建会直接写入 `app/static/`，由 FastAPI 托管：

```powershell
cd frontend
pnpm build
```

## 接入正式模型

编辑 `.env`：

```dotenv
AI_PROVIDER=openai_compatible
AI_API_KEY=your-key
AI_BASE_URL=https://api.openai.com/v1
AI_MODEL=your-model-name
CONTEXT_TOKEN_BUDGET=8000
MIN_RECENT_MESSAGES=6
SUMMARY_MAX_CHARS=1800
```

只要服务实现兼容的 `/chat/completions` 接口即可接入。`deepseek`、`qwen`、`moonshot` 也可直接作为 `AI_PROVIDER` 的别名；角色、Prompt 构造和 API 层不依赖具体模型厂商。

## API 示例

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/v1/chat `
  -ContentType 'application/json' `
  -Body '{"character_id":"su-shi-xuzhou","mode":"tourism","message":"我喜欢诗词，半天怎么游？"}'
```

主要接口：

- `GET /api/v1/characters`
- `GET /api/v1/characters/{character_id}`
- `POST /api/v1/chat`
- `GET /api/v1/sessions/{session_id}`
- `DELETE /api/v1/sessions/{session_id}`

## 测试

```powershell
pytest
```

## 当前首版边界

- 会话已持久化到本地 SQLite（`data/canal.db`），服务重启后会重新加载；但这是匿名浏览器级会话，没有登录体系。
- token 数使用无需绑定特定模型的保守估算，并非厂商 tokenizer 的精确计数。
- `demo` 模式是确定性演示，不是真正的生成式 AI。
- 没有实时景区、票务和交通数据，回答不会编造精确数字，也不反复提示用户核验官方信息。
- 人物卡目前由样例文档人工整理，尚未开放文档自动导入接口。
