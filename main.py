"""
Daily watchlist check.

For each ticker in config.yaml, pulls recent price history, checks for a
moving-average crossover and/or an RSI threshold breach, and if either
fires: opens a GitHub Issue (your approval screen) and sends a short text.

This script does not place trades and does not generate investment advice -
it only flags when a rule YOU defined in config.yaml has been triggered,
so you can decide what (if anything) to do about it.
"""

import sys
from pathlib import Path

import yaml
import yfinance as yf

from indicators import compute_sma, compute_rsi, detect_sma_crossover, detect_rsi_signal
from notify import create_issue, send_sms_via_email


def load_config() -> dict:
    config_path = Path(__file__).parent.parent / "config.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


def check_ticker(ticker: str, cfg: dict) -> list[dict]:
    """Returns a list of triggered signals (possibly empty) for one ticker."""
    ind = cfg["indicators"]
    history = yf.Ticker(ticker).history(period=cfg["lookback_period"])

    if history.empty or len(history) < ind["sma_long"] + 2:
        print(f"[{ticker}] Not enough price history, skipping.")
        return []

    close = history["Close"]
    sma_short = compute_sma(close, ind["sma_short"])
    sma_long = compute_sma(close, ind["sma_long"])
    rsi = compute_rsi(close, ind["rsi_period"])

    signals = []

    crossover = detect_sma_crossover(sma_short, sma_long)
    if crossover:
        signals.append({
            "type": crossover,
            "detail": (
                f"{ind['sma_short']}-day SMA (${sma_short.iloc[-1]:.2f}) crossed "
                f"{'above' if crossover == 'golden_cross' else 'below'} "
                f"{ind['sma_long']}-day SMA (${sma_long.iloc[-1]:.2f})"
            ),
        })

    rsi_signal = detect_rsi_signal(rsi, ind["rsi_oversold"], ind["rsi_overbought"])
    if rsi_signal:
        signals.append({
            "type": rsi_signal,
            "detail": f"RSI({ind['rsi_period']}) is at {rsi.iloc[-1]:.1f}",
        })

    for s in signals:
        s["ticker"] = ticker
        s["price"] = close.iloc[-1]

    return signals


def format_issue(signal: dict) -> tuple[str, str]:
    label_map = {
        "golden_cross": "📈 Golden Cross",
        "death_cross": "📉 Death Cross",
        "oversold": "🟢 RSI Oversold",
        "overbought": "🔴 RSI Overbought",
    }
    title = f"{label_map[signal['type']]} - {signal['ticker']} (${signal['price']:.2f})"
    body = (
        f"**Ticker:** {signal['ticker']}\n"
        f"**Signal:** {signal['type'].replace('_', ' ').title()}\n"
        f"**Detail:** {signal['detail']}\n"
        f"**Price at check:** ${signal['price']:.2f}\n\n"
        f"---\n"
        f"This is an automated flag based on the rules in `config.yaml`. "
        f"It is not investment advice - review and decide for yourself, "
        f"then execute manually in your brokerage if you choose to act on it.\n\n"
        f"Comment or close this issue once you've reviewed it."
    )
    return title, body


def main():
    cfg = load_config()
    all_signals = []

    for ticker in cfg["watchlist"]:
        try:
            all_signals.extend(check_ticker(ticker, cfg))
        except Exception as e:
            print(f"[{ticker}] Error checking ticker: {e}")

    if not all_signals:
        print("No signals triggered today.")
        return

    issue_links = []
    for signal in all_signals:
        title, body = format_issue(signal)
        url = create_issue(title, body)
        print(f"Created issue: {url}")
        if url:
            issue_links.append((signal["ticker"], signal["type"], url))

    if issue_links:
        lines = [f"{t} {s.replace('_', ' ')}" for t, s, _ in issue_links]
        text_body = "Trade watch: " + "; ".join(lines) + ". Check GitHub for details."
        sent = send_sms_via_email(text_body[:300])  # keep it short for carrier limits
        print("SMS sent." if sent else "SMS failed to send.")


if __name__ == "__main__":
    sys.exit(main())
