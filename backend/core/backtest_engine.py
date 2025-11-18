"""回测引擎封装"""
import os
import sys
from pathlib import Path
from typing import Dict, List, Callable, Any
from collections import defaultdict
from dotenv import load_dotenv

# 添加项目根目录到路径
BASE_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

load_dotenv()

from main import (
    LLMs,
    AccountInfoLLMs,
    ProfitInfoLLMs,
    initialize_llm_info,
    initialize_profit_info,
    market_trading_parallel,
)
from utils.get_stocks_info import get_stocks_info
from backend.core.models import BacktestConfig, BacktestStatus
from backend.config import RESULTS_DIR, CKPT_DIR


class BacktestEngine:
    """回测引擎封装类"""
    
    def __init__(self, config: BacktestConfig):
        self.config = config
        self.task_id = None
        self.status = BacktestStatus.PENDING
        
    def prepare_models(self, selected_models: List[str]) -> Dict:
        """准备要运行的模型"""
        available_models = {
            "qwen": LLMs.get("qwen"),
            "deepseek": LLMs.get("deepseek"),
            "kimi": LLMs.get("kimi"),
            "chatglm": LLMs.get("chatglm"),
        }
        
        # 过滤出选中的模型
        selected_llms = {
            model: client
            for model, client in available_models.items()
            if model in selected_models and client is not None
        }
        
        return selected_llms
    
    def run_backtest(
        self,
        task_id: str,
        progress_callback: Callable[[Dict], None] = None
    ) -> Dict[str, Any]:
        """运行回测任务"""
        self.task_id = task_id
        self.status = BacktestStatus.RUNNING
        
        try:
            # 准备模型
            selected_llms = self.prepare_models(self.config.models)
            if not selected_llms:
                raise ValueError("没有可用的模型")
            
            # 临时设置 LLMs（在任务中使用的模型）
            global LLMs
            original_llms = LLMs.copy()
            LLMs = selected_llms
            
            # 初始化账户信息
            AccountInfoLLMs.clear()
            ProfitInfoLLMs.clear()
            
            AccountInfoLLMs.update(
                initialize_llm_info(
                    selected_llms,
                    self.config.initial_cash,
                    AccountInfoLLMs=AccountInfoLLMs,
                    resume_from_ckpt=False  # 不从checkpoint恢复
                )
            )
            ProfitInfoLLMs.update(
                initialize_profit_info(
                    ProfitInfoLLMs=ProfitInfoLLMs,
                    resume_from_ckpt=False
                ) or {}
            )
            
            # 获取股票数据
            stocks_dict, all_stocks_names = get_stocks_info(
                stocks_root=str(BASE_DIR / "original_data"),
                start_date=self.config.start_date,
                end_date=self.config.end_date
            )
            
            # 清空 checkpoint 目录（确保从新开始）
            for ckpt_file in (CKPT_DIR / "AccountInfoLLMs").glob("*.json"):
                ckpt_file.unlink()
            for ckpt_file in (CKPT_DIR / "ProfitInfoLLMs").glob("*.json"):
                ckpt_file.unlink()
            
            # 运行并行回测
            market_trading_parallel(
                AccountInfoLLMs,
                ProfitInfoLLMs,
                stocks_dict,
                history=self.config.history,
                debug=self.config.debug,
                max_workers=len(selected_llms)
            )
            
            # 收集结果文件路径
            result_files = []
            for model_name in selected_llms.keys():
                result_file = RESULTS_DIR / f"{model_name}.csv"
                if result_file.exists():
                    result_files.append(str(result_file.relative_to(BASE_DIR)))
            
            self.status = BacktestStatus.COMPLETED
            
            # 恢复原始 LLMs
            LLMs = original_llms
            
            return {
                "status": BacktestStatus.COMPLETED,
                "result_files": result_files,
                "models": list(selected_llms.keys())
            }
            
        except Exception as e:
            self.status = BacktestStatus.FAILED
            return {
                "status": BacktestStatus.FAILED,
                "error": str(e)
            }
    
    def stop(self):
        """停止回测（预留功能）"""
        # TODO: 实现停止逻辑
        self.status = BacktestStatus.STOPPED

