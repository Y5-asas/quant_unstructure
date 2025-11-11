"""Daily economic indicator utilities for AlphaArena backtesting."""
import argparse
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd


def compute_sma(series: pd.Series, window: int) -> pd.Series:
    """Simple moving average."""
    return series.rolling(window=window, min_periods=window).mean()


def compute_ema(series: pd.Series, span: int) -> pd.Series:
    """Exponential moving average with a given span."""
    return series.ewm(span=span, adjust=False, min_periods=span).mean()


def compute_macd(
    series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
) -> pd.DataFrame:
    """Return MACD, signal and histogram as columns."""

    ema_fast = compute_ema(series, fast)
    ema_slow = compute_ema(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False, min_periods=signal).mean()
    hist = macd_line - signal_line
    return pd.DataFrame({"macd": macd_line, "signal": signal_line, "hist": hist})


def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Relative Strength Index."""

    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Average True Range."""

    high_low = df["high"] - df["low"]
    high_prev_close = (df["high"] - df["close"].shift(1)).abs()
    low_prev_close = (df["low"] - df["close"].shift(1)).abs()
    true_range = pd.concat([high_low, high_prev_close, low_prev_close], axis=1).max(axis=1)
    atr = true_range.rolling(window=period, min_periods=period).mean()
    return atr


def compute_rolling_volatility(series: pd.Series, window: int = 20) -> pd.Series:
    """Return rolling volatility (annualised) based on percentage change."""

    rolling_std = series.pct_change().rolling(window=window, min_periods=window).std()
    return rolling_std * (window ** 0.5)


def enrich_daily_indicators(
    df: pd.DataFrame,
    sma_windows: Iterable[int] = (5, 10, 20),
    ema_windows: Iterable[int] = (5, 10, 20),
    rsi_periods: Iterable[int] = (14,),
    volatility_window: int = 20,
) -> pd.DataFrame:
    """Return dataframe with standard technical indicators appended."""

    indicators = df.copy().sort_values("date").reset_index(drop=True)
    close = indicators["close"]

    for window in sma_windows:
        indicators[f"sma_{window}"] = compute_sma(close, window)

    for span in ema_windows:
        indicators[f"ema_{span}"] = compute_ema(close, span)

    macd_df = compute_macd(close)
    indicators = pd.concat([indicators, macd_df.add_prefix("macd_")], axis=1)

    for period in rsi_periods:
        indicators[f"rsi_{period}"] = compute_rsi(close, period)

    indicators["atr_14"] = compute_atr(indicators, period=14)
    indicators["volatility_annualized"] = compute_rolling_volatility(
        close, window=volatility_window
    )

    return indicators


def load_csv_with_indicators(csv_path: Path) -> pd.DataFrame:
    """Convenience helper for quick inspection from CLI."""

    df = pd.read_csv(csv_path)
    if "date" not in df.columns:
        raise ValueError("CSV must contain a 'date' column")
    return enrich_daily_indicators(df)


def main(argv: Optional[Iterable[str]] = None) -> None:
    """CLI entry for debugging (reads CSV and prints first rows with indicators)."""

    import argparse

    parser = argparse.ArgumentParser(description="Compute daily indicators for a CSV")
    parser.add_argument(
        "csv",
        type=Path,
        nargs="?",
        default=Path(__file__).resolve().parents[1] / "original_data" / "AAPL.csv",
        help="Path to CSV (default: original_data/AAPL.csv)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path to save the enriched CSV",
    )
    args = parser.parse_args(argv)

    df = load_csv_with_indicators(args.csv)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(args.output, index=False)
        print(f"Saved indicators to {args.output}")
    else:
        print(df.head(10))


if __name__ == "__main__":
    main()
