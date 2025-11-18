"""模型管理路由"""
from fastapi import APIRouter
from typing import List

router = APIRouter()


@router.get("/list")
async def list_models():
    """
    获取所有可用模型列表
    
    Returns:
        模型列表
    """
    return {
        "models": [
            {
                "id": "qwen",
                "name": "Qwen",
                "description": "阿里通义千问模型"
            },
            {
                "id": "deepseek",
                "name": "DeepSeek",
                "description": "DeepSeek AI 模型"
            },
            {
                "id": "kimi",
                "name": "Kimi",
                "description": "Kimi AI 模型"
            },
            {
                "id": "chatglm",
                "name": "ChatGLM",
                "description": "智谱AI ChatGLM 模型"
            }
        ]
    }

