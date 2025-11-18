"""回测相关路由"""
import uuid
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any
from datetime import datetime
from backend.core.models import BacktestConfig, BacktestTask, BacktestStatus
from backend.core.backtest_engine import BacktestEngine

router = APIRouter()

# 任务存储（内存中，生产环境应使用 Redis 或数据库）
tasks: Dict[str, BacktestTask] = {}
engines: Dict[str, BacktestEngine] = {}


@router.post("/start", response_model=BacktestTask)
async def start_backtest(
    config: BacktestConfig,
    background_tasks: BackgroundTasks
):
    """
    启动回测任务
    
    Args:
        config: 回测配置
        
    Returns:
        任务信息
    """
    # 生成任务 ID
    task_id = str(uuid.uuid4())
    
    # 创建回测引擎
    engine = BacktestEngine(config)
    engines[task_id] = engine
    
    # 创建任务记录
    task = BacktestTask(
        task_id=task_id,
        config=config,
        status=BacktestStatus.PENDING,
        created_at=datetime.now()
    )
    tasks[task_id] = task
    
    # 在后台运行回测
    def run_backtest():
        try:
            task.status = BacktestStatus.RUNNING
            task.started_at = datetime.now()
            
            result = engine.run_backtest(task_id)
            
            task.status = result["status"]
            task.completed_at = datetime.now()
            if "result_files" in result:
                task.result_files = result["result_files"]
            if "error" in result:
                task.error = result["error"]
        except Exception as e:
            task.status = BacktestStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.now()
    
    background_tasks.add_task(run_backtest)
    
    return task


@router.get("/status/{task_id}", response_model=BacktestTask)
async def get_task_status(task_id: str):
    """
    查询任务状态
    
    Args:
        task_id: 任务 ID
        
    Returns:
        任务信息
    """
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return tasks[task_id]


@router.post("/stop/{task_id}", response_model=BacktestTask)
async def stop_backtest(task_id: str):
    """
    停止回测任务（预留功能）
    
    Args:
        task_id: 任务 ID
        
    Returns:
        任务信息
    """
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = tasks[task_id]
    if task.status not in [BacktestStatus.PENDING, BacktestStatus.RUNNING]:
        raise HTTPException(status_code=400, detail="任务无法停止")
    
    # 停止引擎
    if task_id in engines:
        engines[task_id].stop()
    
    task.status = BacktestStatus.STOPPED
    task.completed_at = datetime.now()
    
    return task


@router.get("/results/{task_id}")
async def get_results(task_id: str):
    """
    获取回测结果
    
    Args:
        task_id: 任务 ID
        
    Returns:
        结果文件列表和下载链接
    """
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = tasks[task_id]
    if task.status != BacktestStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"任务尚未完成，当前状态: {task.status}"
        )
    
    return {
        "task_id": task_id,
        "result_files": task.result_files,
        "models": task.config.models
    }

