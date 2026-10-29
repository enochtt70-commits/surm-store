# app/utils/helpers.py
from datetime import date


def format_currency(amount, symbol="GHS"):
    try:
        return f"{symbol} {float(amount):,.2f}"
    except (TypeError, ValueError):
        return f"{symbol} 0.00"


def current_month_range():
    today = date.today()
    return today.replace(day=1), today


def safe_float(val, default=0.0):
    try:
        return float(val)
    except (TypeError, ValueError):
        return default
