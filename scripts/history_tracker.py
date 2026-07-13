#!/usr/bin/env python3
"""
期货基本面日报 - 历史数据回溯模块
维护品种历史价格数据库，计算价格分位图
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
HISTORY_DIR = DATA_DIR / "history"

# 确保历史数据目录存在
HISTORY_DIR.mkdir(exist_ok=True)


def load_price_history(code):
    """
    加载品种历史价格数据
    返回: list of dict [{"date": str, "close": float, "change_pct": float}]
    """
    history_file = HISTORY_DIR / f"{code}_history.json"
    if not history_file.exists():
        return []
    
    with open(history_file, "r", encoding="utf-8") as f:
        return json.load(f)


def save_price_history(code, new_data):
    """
    保存品种历史价格数据
    new_data: dict {"date": str, "close": float, "change_pct": float}
    """
    history = load_price_history(code)
    
    # 去重：如果日期已存在，更新；否则追加
    date_exists = False
    for i, record in enumerate(history):
        if record["date"] == new_data["date"]:
            history[i] = new_data
            date_exists = True
            break
    
    if not date_exists:
        history.append(new_data)
    
    # 按日期排序
    history.sort(key=lambda x: x["date"])
    
    # 保存
    history_file = HISTORY_DIR / f"{code}_history.json"
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    
    return history


def update_all_histories(quotes_data):
    """
    更新所有品种的历史数据
    quotes_data: {code: {"close": float, "change_pct": float, "date": str}}
    """
    for code, quote in quotes_data.items():
        new_record = {
            "date": quote.get("date", datetime.now().strftime("%Y%m%d")),
            "close": quote.get("close", 0),
            "change_pct": quote.get("change_pct", 0),
            "volume": quote.get("volume", 0),
            "open_interest": quote.get("open_interest", 0)
        }
        save_price_history(code, new_record)


def calculate_price_percentile(code, current_price, period_days=252):
    """
    计算价格历史分位
    返回: dict {
        "percentile_1y": float,  # 近1年分位
        "percentile_3y": float,  # 近3年分位（如有数据）
        "percentile_all": float, # 全历史分位
        "avg_20d": float,        # 20日均线
        "avg_60d": float,        # 60日均线
        "volatility_20d": float, # 20日波动率
        "max_1y": float,         # 近1年最高
        "min_1y": float,         # 近1年最低
    }
    """
    history = load_price_history(code)
    if not history:
        return {}
    
    result = {}
    
    # 提取收盘价列表
    closes = [h["close"] for h in history if "close" in h]
    if not closes:
        return {}
    
    # 全历史分位
    sorted_closes = sorted(closes)
    n = len(sorted_closes)
    if n > 0:
        # 找到当前价格的位置
        position = sum(1 for c in sorted_closes if c < current_price)
        result["percentile_all"] = round(position / n * 100, 1)
    
    # 近1年分位（约252个交易日）
    closes_1y = closes[-min(252, n):]
    if closes_1y:
        sorted_1y = sorted(closes_1y)
        position_1y = sum(1 for c in sorted_1y if c < current_price)
        result["percentile_1y"] = round(position_1y / len(sorted_1y) * 100, 1)
        result["max_1y"] = max(closes_1y)
        result["min_1y"] = min(closes_1y)
    
    # 近3年分位
    closes_3y = closes[-min(756, n):]
    if closes_3y and len(closes_3y) > len(closes_1y):
        sorted_3y = sorted(closes_3y)
        position_3y = sum(1 for c in sorted_3y if c < current_price)
        result["percentile_3y"] = round(position_3y / len(sorted_3y) * 100, 1)
    
    # 移动平均线
    if len(closes) >= 20:
        result["avg_20d"] = round(sum(closes[-20:]) / 20, 2)
    if len(closes) >= 60:
        result["avg_60d"] = round(sum(closes[-60:]) / 60, 2)
    
    # 20日波动率（标准差/均值）
    if len(closes) >= 20:
        recent = closes[-20:]
        avg = sum(recent) / len(recent)
        variance = sum((c - avg) ** 2 for c in recent) / len(recent)
        std = variance ** 0.5
        result["volatility_20d"] = round(std / avg * 100, 2) if avg > 0 else 0
    
    # 趋势判断
    if "avg_20d" in result and "avg_60d" in result:
        if result["avg_20d"] > result["avg_60d"]:
            result["trend"] = "多头排列"
        elif result["avg_20d"] < result["avg_60d"]:
            result["trend"] = "空头排列"
        else:
            result["trend"] = "趋势不明"
    
    return result


def get_price_position_text(code, current_price):
    """
    获取价格位置描述文本
    """
    percentile = calculate_price_percentile(code, current_price)
    if not percentile:
        return "暂无历史数据"
    
    parts = []
    
    if "percentile_1y" in percentile:
        parts.append(f"近1年分位 {percentile['percentile_1y']:.0f}%")
    
    if "percentile_3y" in percentile:
        parts.append(f"近3年分位 {percentile['percentile_3y']:.0f}%")
    
    if "trend" in percentile:
        parts.append(f"均线{percentile['trend']}")
    
    return "，".join(parts) if parts else "暂无历史数据"


def generate_price_history_chart_data(code, days=60):
    """
    生成价格历史图表数据（用于前端展示）
    返回: list of dict [{"date": str, "close": float, "ma20": float}]
    """
    history = load_price_history(code)
    if not history:
        return []
    
    # 取最近N天
    recent = history[-min(days, len(history)):]
    
    chart_data = []
    for i, record in enumerate(recent):
        item = {
            "date": record["date"],
            "close": record["close"]
        }
        
        # 计算MA20（如果数据足够）
        idx = history.index(record)
        if idx >= 19:
            ma20_closes = [h["close"] for h in history[idx-19:idx+1]]
            item["ma20"] = round(sum(ma20_closes) / 20, 2)
        
        chart_data.append(item)
    
    return chart_data


if __name__ == "__main__":
    # 测试
    test_code = "CU"
    history = load_price_history(test_code)
    print(f"{test_code} 历史数据: {len(history)} 条")
    
    if history:
        latest = history[-1]
        percentile = calculate_price_percentile(test_code, latest["close"])
        print(f"价格分位: {json.dumps(percentile, ensure_ascii=False, indent=2)}")
