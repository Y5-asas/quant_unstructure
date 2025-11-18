"""FastAPI 主应用"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import CORS_ORIGINS
from backend.api.routes import backtest, models, data

app = FastAPI(
    title="Alpha Arena API",
    description="AI Trading Backtesting Platform",
    version="1.0.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(backtest.router, prefix="/api/backtest", tags=["backtest"])
app.include_router(models.router, prefix="/api/models", tags=["models"])
app.include_router(data.router, prefix="/api/data", tags=["data"])


@app.get("/")
async def root():
    """API 根路径"""
    return {
        "message": "Alpha Arena API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    from backend.config import API_HOST, API_PORT
    uvicorn.run(app, host=API_HOST, port=API_PORT)

