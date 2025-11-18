"""后端配置文件"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 项目根目录
BASE_DIR = Path(__file__).parent.parent

# 回测相关配置
RESULTS_DIR = BASE_DIR / "results"
CKPT_DIR = BASE_DIR / "ckpt"
ORIGINAL_DATA_DIR = BASE_DIR / "original_data"

# API 配置
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# CORS 配置
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]

# Celery 配置
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

# 数据库配置（预留）
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./alpha_arena.db")

# 实时股票数据接口配置（预留，当前不使用）
STOCK_DATA_SOURCE = os.getenv("STOCK_DATA_SOURCE", "local")  # local/realtime
STOCK_API_KEY = os.getenv("STOCK_API_KEY", "")

