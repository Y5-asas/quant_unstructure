"""股票数据接口路由（预留实时股票接口）"""
from fastapi import APIRouter, HTTPException
from typing import List
from backend.core.data_source import get_stock_data_source
from backend.core.models import RealtimeStockData

router = APIRouter()


@router.get("/realtime/{symbol}")
async def get_realtime_data(symbol: str):
    """
    获取实时股票数据（预留接口，当前不支持）
    
    Args:
        symbol: 股票代码，如 "AAPL"
        
    Returns:
        实时股票数据
    """
    try:
        data_source = get_stock_data_source()
        result = data_source.get_realtime_data([symbol])
        return result.get(symbol)
    except NotImplementedError:
        raise HTTPException(
            status_code=501,
            detail="实时数据接口尚未实现，请使用历史数据"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/historical/{symbol}")
async def get_historical_data(symbol: str, start_date: str, end_date: str):
    """
    获取历史股票数据（预留接口，当前使用本地CSV）
    
    Args:
        symbol: 股票代码，如 "AAPL"
        start_date: 开始日期 "YYYY-MM-DD"
        end_date: 结束日期 "YYYY-MM-DD"
        
    Returns:
        历史K线数据
    """
    try:
        data_source = get_stock_data_source()
        df = data_source.get_historical_data(symbol, start_date, end_date)
        return df.to_dict("records")
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/subscribe")
async def subscribe_realtime_updates(symbols: List[str]):
    """
    订阅实时股票数据更新（预留接口）
    
    Args:
        symbols: 股票代码列表
        
    Returns:
        订阅信息
    """
    try:
        data_source = get_stock_data_source()
        # TODO: 实现订阅逻辑
        raise NotImplementedError("实时订阅接口尚未实现")
    except NotImplementedError:
        raise HTTPException(
            status_code=501,
            detail="实时订阅接口尚未实现"
        )

