# Alpha Arena Web App 实施指南

## 项目结构

```
quant_unstructure/
├── backend/              # 后端代码
│   ├── api/              # FastAPI 应用
│   │   ├── main.py       # 主应用入口
│   │   └── routes/       # 路由定义
│   │       ├── backtest.py    # 回测相关接口
│   │       ├── models.py      # 模型管理接口
│   │       └── data.py        # 数据接口（预留实时股票）
│   ├── core/             # 核心逻辑
│   │   ├── models.py     # 数据模型定义
│   │   ├── backtest_engine.py  # 回测引擎封装
│   │   └── data_source.py      # 数据源抽象（预留实时接口）
│   ├── config.py         # 配置文件
│   └── requirements.txt  # Python 依赖
├── frontend/             # 前端代码
│   ├── src/
│   │   ├── components/   # React 组件
│   │   │   ├── BacktestConfig.tsx
│   │   │   ├── ProgressPanel.tsx
│   │   │   ├── ProfitChart.tsx
│   │   │   ├── ModelCards.tsx
│   │   │   └── Leaderboard.tsx
│   │   ├── services/     # API 服务
│   │   │   ├── api.ts
│   │   │   └── websocket.ts
│   │   └── App.tsx       # 主应用组件
│   ├── package.json
│   └── vite.config.ts
└── WEB_APP_PLAN.md       # 技术规划文档
```

## 快速开始

### 1. 后端设置

```bash
# 安装依赖
cd backend
pip install -r requirements.txt

# 运行后端（开发模式）
python -m backend.api.main
# 或使用 uvicorn
uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000

# 访问 API 文档
# http://localhost:8000/docs
```

### 2. 前端设置

```bash
# 安装依赖
cd frontend
npm install

# 启动开发服务器
npm run dev

# 访问前端
# http://localhost:5173
```

## 当前功能

### 已完成
- ✅ 后端 API 框架（FastAPI）
- ✅ 回测任务管理（启动/查询/停止）
- ✅ 回测引擎封装（使用现有 main.py 逻辑）
- ✅ 前端项目结构（React + TypeScript + Vite）
- ✅ API 服务封装
- ⚠️ 数据源抽象层（预留实时股票接口位置）

### 待实现
- ⏳ WebSocket 实时推送进度
- ⏳ 前端 UI 组件（配置面板、图表、模型卡片）
- ⏳ 任务队列（Celery + Redis）用于长时间任务
- ⏳ 数据库存储任务历史（SQLite）
- ⏳ 实时股票数据接口（目前使用本地 CSV）

## API 接口说明

### 回测相关

#### POST /api/backtest/start
启动回测任务

**请求体：**
```json
{
  "start_date": "2025-01-01",
  "end_date": "2025-04-29",
  "initial_cash": 100000.0,
  "models": ["qwen", "deepseek", "kimi", "chatglm"],
  "history": 10,
  "debug": false
}
```

**响应：**
```json
{
  "task_id": "uuid-string",
  "config": {...},
  "status": "pending",
  "created_at": "2025-11-12T10:00:00"
}
```

#### GET /api/backtest/status/{task_id}
查询任务状态

#### POST /api/backtest/stop/{task_id}
停止任务

#### GET /api/backtest/results/{task_id}
获取回测结果

### 模型管理

#### GET /api/models/list
获取可用模型列表

### 数据接口（预留）

#### GET /api/data/realtime/{symbol}
获取实时股票数据（当前返回 501 错误）

#### GET /api/data/historical/{symbol}
获取历史股票数据（当前使用本地 CSV）

## 实时股票接口预留位置

所有实时股票数据相关的代码应放在：

1. **数据源抽象**: `backend/core/data_source.py`
   - 定义了 `StockDataSource` 抽象基类
   - 当前实现 `LocalStockDataSource`（使用 CSV）
   - 未来可实现 `RealtimeStockDataSource`

2. **API 路由**: `backend/api/routes/data.py`
   - `/api/data/realtime/{symbol}` - 获取实时数据
   - `/api/data/historical/{symbol}` - 获取历史数据
   - `/api/data/subscribe` - 订阅实时更新

3. **配置**: `backend/config.py`
   - `STOCK_DATA_SOURCE` - 数据源类型（local/realtime）
   - `STOCK_API_KEY` - API 密钥配置

## 下一步开发建议

### Phase 1: 完善后端（1-2天）
1. 集成 Celery 任务队列
2. 实现 WebSocket 进度推送
3. 添加数据库存储任务历史

### Phase 2: 前端基础界面（2-3天）
1. 回测配置组件
2. 进度展示面板
3. 盈利曲线图表（使用 Recharts）

### Phase 3: 完善功能（1-2天）
1. 模型详情卡片
2. 排行榜
3. UI/UX 优化

### Phase 4: 实时股票接口（可选）
1. 选择数据源（Yahoo Finance / Alpha Vantage / Tushare）
2. 实现数据源接口
3. 添加实时订阅功能

## 注意事项

1. **环境变量**: 确保 `.env` 文件包含所有必要的 API 密钥
2. **数据路径**: 确保 `original_data/` 目录包含股票 CSV 文件
3. **并发限制**: Kimi 等模型有并发限制，注意错误处理
4. **任务存储**: 当前使用内存存储，生产环境应使用 Redis 或数据库

## 参考文档

- FastAPI: https://fastapi.tiangolo.com/
- React: https://react.dev/
- Recharts: https://recharts.org/
- nof1.ai: https://nof1.ai/

