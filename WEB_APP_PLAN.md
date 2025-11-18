# Alpha Arena Web App 技术规划

## 一、整体架构

```
┌─────────────────┐
│   Frontend      │  React + TypeScript + Chart.js/ECharts
│   (Web UI)      │  - 回测配置界面
└────────┬────────┘  - 实时进度展示
         │           - 盈利曲线图表
         │ HTTP/WebSocket
         │
┌────────▼────────────────────────┐
│   Backend API                   │  FastAPI + Python
│   (Flask/FastAPI)               │  - RESTful API
│                                 │  - WebSocket 实时推送
└────────┬────────────────────────┘
         │
    ┌────┴────────────────────────────────┐
    │                                     │
┌───▼──────────┐              ┌──────────▼─────────┐
│  任务管理     │              │   数据存储          │
│  (Celery)    │              │   - SQLite/JSON    │
│              │              │   - results/*.csv  │
└──────────────┘              └────────────────────┘
         │
┌────────▼──────────────┐
│   核心回测引擎         │
│   (现有 main.py)      │
│   - market_trading    │
│   - 多模型并行         │
└───────────────────────┘
```

## 二、功能模块

### 2.1 前端功能
1. **回测配置面板**
   - 日期范围选择（start_date, end_date）
   - 初始资金设置（INITIAL_CASH）
   - 选择要运行的模型（多选：qwen, deepseek, kimi, chatglm）
   - 历史窗口大小（history）
   - 启动/停止按钮

2. **实时进度展示**
   - 当前交易日进度（X/Y 日）
   - 各模型的运行状态（运行中/完成/错误）
   - 实时日志输出

3. **盈利曲线图表**（参考 nof1.ai）
   - 多模型对比折线图
   - X轴：交易日期
   - Y轴：账户总价值（AccountValue）或收益率（ReturnPercent）
   - 可切换显示不同指标
   - 悬停显示详细数据

4. **模型详情卡片**
   - 每个模型的单独卡片
   - 显示当前收益率、可用现金、账户价值
   - 当前持仓列表
   - 交易历史记录

5. **排行榜/对比表**
   - 按收益率排序
   - Sharpe Ratio、最大回撤等指标对比

### 2.2 后端 API 设计

#### RESTful Endpoints:

```
POST   /api/backtest/start          # 启动回测任务
GET    /api/backtest/status/{task_id}  # 查询任务状态
POST   /api/backtest/stop/{task_id}    # 停止任务
GET    /api/backtest/results/{task_id} # 获取回测结果
GET    /api/models                    # 获取所有可用模型列表
GET    /api/history                   # 获取历史回测记录
```

#### WebSocket:
```
WS     /ws/progress/{task_id}        # 实时推送进度更新
WS     /ws/live                       # 实时推送各模型状态
```

## 三、技术栈选择

### 后端
- **FastAPI** - 现代 Python Web 框架，支持异步、自动 API 文档
- **Celery** - 后台任务队列，处理长时间运行的回测任务
- **Redis** - 作为 Celery broker 和结果存储
- **SQLite** - 存储任务元数据和历史记录
- **WebSocket** - 实时推送进度和状态

### 前端
- **React 18** + **TypeScript** - UI 框架
- **Vite** - 构建工具
- **Chart.js** 或 **ECharts** - 图表库
- **Ant Design** 或 **Material-UI** - UI 组件库
- **Axios** - HTTP 客户端
- **Socket.io-client** - WebSocket 客户端

## 四、数据流设计

### 4.1 任务启动流程
```
1. 前端提交配置 → POST /api/backtest/start
2. 后端创建 Celery 任务 → 返回 task_id
3. 前端建立 WebSocket 连接 → ws/progress/{task_id}
4. 后端启动回测进程（调用 market_trading_parallel）
5. 实时推送进度 → WebSocket
6. 定期保存结果到 results/*.csv
7. 任务完成 → 推送最终结果
```

### 4.2 数据存储结构

#### 任务元数据（SQLite）:
```sql
CREATE TABLE backtest_tasks (
    id TEXT PRIMARY KEY,
    config JSON,           -- 回测配置
    status TEXT,           -- pending/running/completed/failed
    created_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    models TEXT[],         -- 运行的模型列表
    result_files TEXT[]    -- 生成的CSV文件路径
);
```

#### 结果文件（CSV）:
- 保持现有格式：`results/{model}.csv`
- 包含列：Date, ReturnPercent, AvailableCash, AccountValue

## 五、实时股票接口预留

### 5.1 接口设计（暂不实现，预留位置）

#### 数据源接口抽象:
```python
# api/data_source.py (预留)
class StockDataSource:
    """股票数据源抽象基类"""
    def get_realtime_data(self, symbols: List[str]) -> Dict:
        """获取实时股票数据"""
        pass
    
    def get_historical_data(self, symbol: str, start: str, end: str) -> pd.DataFrame:
        """获取历史数据"""
        pass

# 可能的实现：
# - Yahoo Finance API
# - Alpha Vantage
# - Tushare（国内）
# - 自建数据采集服务
```

#### API Endpoints（预留）:
```
GET  /api/data/realtime/{symbol}       # 获取实时股价
GET  /api/data/historical/{symbol}     # 获取历史K线
POST /api/data/subscribe               # 订阅实时更新
```

## 六、项目结构

```
quant_unstructure/
├── backend/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI 主应用
│   │   ├── routes/
│   │   │   ├── backtest.py      # 回测相关路由
│   │   │   ├── models.py        # 模型管理路由
│   │   │   └── data.py          # 数据接口路由（预留）
│   │   ├── websocket.py         # WebSocket 处理
│   │   └── tasks.py             # Celery 任务定义
│   ├── core/
│   │   ├── backtest_engine.py   # 回测引擎封装
│   │   ├── data_source.py       # 数据源抽象（预留）
│   │   └── models.py            # 数据模型
│   ├── db/
│   │   └── database.py          # 数据库连接和模型
│   └── config.py                # 配置文件
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── BacktestConfig.tsx
│   │   │   ├── ProgressPanel.tsx
│   │   │   ├── ProfitChart.tsx
│   │   │   ├── ModelCards.tsx
│   │   │   └── Leaderboard.tsx
│   │   ├── services/
│   │   │   ├── api.ts
│   │   │   └── websocket.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
├── utils/                         # 现有工具函数
├── llm/                         # 现有LLM接口
├── results/                     # 回测结果
├── requirements.txt             # Python 依赖
└── README.md
```

## 七、实施步骤

### Phase 1: 基础后端 API（1-2天）
1. 搭建 FastAPI 框架
2. 创建基础的 REST API（启动/查询任务）
3. 封装现有回测逻辑为独立函数
4. 实现任务状态管理

### Phase 2: 任务队列集成（1天）
1. 配置 Celery + Redis
2. 将回测任务改为异步任务
3. 实现任务进度追踪

### Phase 3: WebSocket 实时推送（1天）
1. 集成 WebSocket 支持
2. 实现进度实时推送
3. 前端建立连接并接收数据

### Phase 4: 前端基础界面（2-3天）
1. 搭建 React 项目
2. 创建回测配置组件
3. 实现进度展示面板
4. 集成图表库展示盈利曲线

### Phase 5: 完善和优化（1-2天）
1. 添加模型详情卡片
2. 实现排行榜功能
3. 错误处理和用户提示
4. UI/UX 优化

## 八、参考设计（nof1.ai）
- 主面板：大的折线图展示账户总价值
- 模型列表：横向卡片展示各个模型
- 实时更新：WebSocket 推送最新数据
- 简洁现代：深色主题，清晰的数值展示

## 九、预留接口位置

所有实时股票数据相关的接口代码应放在：
- `backend/api/routes/data.py` - API 路由
- `backend/core/data_source.py` - 数据源抽象
- 配置项在 `backend/config.py` 中预留

当前阶段：所有 `data_source.py` 中的方法返回占位符或使用 `original_data/` 目录的 CSV 文件。

