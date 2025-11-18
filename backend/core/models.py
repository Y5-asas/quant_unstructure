"""数据模型定义"""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class BacktestStatus(str, Enum):
    """回测任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


class BacktestConfig(BaseModel):
    """回测配置"""
    start_date: str  # "2025-01-01"
    end_date: str    # "2025-04-29"
    initial_cash: float = 100000.0
    models: List[str] = ["qwen", "deepseek", "kimi", "chatglm"]
    history: int = 10  # 历史窗口大小
    debug: bool = False


class BacktestTask(BaseModel):
    """回测任务信息"""
    task_id: str
    config: BacktestConfig
    status: BacktestStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: Dict[str, Any] = {}  # 当前进度信息
    result_files: List[str] = []   # 结果文件路径
    error: Optional[str] = None


class ProgressUpdate(BaseModel):
    """进度更新"""
    task_id: str
    current_day: int
    total_days: int
    models_status: Dict[str, str]  # 各模型状态
    message: str


class ModelResult(BaseModel):
    """模型回测结果"""
    model_name: str
    date: str
    return_percent: float
    available_cash: float
    account_value: float
    positions: Dict[str, Any] = {}


# 预留：实时股票数据接口模型
class RealtimeStockData(BaseModel):
    """实时股票数据（预留）"""
    symbol: str
    price: float
    volume: int
    timestamp: datetime
    # ... 其他字段待扩展

