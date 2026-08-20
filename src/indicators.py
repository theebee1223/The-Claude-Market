"""
Technical indicator calculations.

These are pure math on price history - no trading logic or recommendations
live here. main.py decides what to do with the numbers.
"""

import pandas as pd


def compute_sma(close: pd.Series, window: int) -> pd.Series:
    """Simple moving average over `window` days."""
    return close.rolling(window=window).mean()


def compute_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """
    Relative Strength Index (Wilder's smoothing method).
    Returns a 0-100 series; NaN for the first `period` rows.
    """
    delta = close.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    # Where avg_loss is 0 (no losses in window), RSI is 100
    rsi = rsi.where(avg_loss != 0, 100)
    return rsi


def detect_sma_crossover(sma_short: pd.Series, sma_long: pd.Series) -> str | None:
    """
    Checks the most recent two rows for a crossover event.
    Returns "golden_cross", "death_cross", or None.
    """
    if len(sma_short) < 2 or len(sma_long) < 2:
        return None

    prev_short, prev_long = sma_short.iloc[-2], sma_long.iloc[-2]
    curr_short, curr_long = sma_short.iloc[-1], sma_long.iloc[-1]

    if pd.isna(prev_short) or pd.isna(prev_long) or pd.isna(curr_short) or pd.isna(curr_long):
        return None

    if prev_short <= prev_long and curr_short > curr_long:
        return "golden_cross"
    if prev_short >= prev_long and curr_short < curr_long:
        return "death_cross"
    return None


def detect_rsi_signal(rsi: pd.Series, oversold: float, overbought: float) -> str | None:
    """Returns 'oversold', 'overbought', or None based on the latest RSI reading."""
    if len(rsi) == 0 or pd.isna(rsi.iloc[-1]):
        return None

    latest = rsi.iloc[-1]
    if latest <= oversold:
        return "oversold"
    if latest >= overbought:
        return "overbought"
    return None
