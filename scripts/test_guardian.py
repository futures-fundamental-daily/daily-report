#!/usr/bin/env python3
"""测试数据守护者模块 - 修正版"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
import json

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
sys.path.insert(0, str(BASE_DIR / "scripts"))

from fetcher import load_config
from data_guardian import (
    detect_single_day_stale, detect_consecutive_stale,
    detect_frozen_data, detect_mock_fallback, _compute_data_fingerprint
)

config = load_config()
products = config["products"]

# 加载指定日期的数据
def load_quotes(date_str):
    f = DATA_DIR / f"quotes_{date_str}.json"
    if f.exists():
        with open(f, "r", encoding="utf-8") as fh:
            return json.load(fh)
    return None

# 对比指定两天
def test_date_pair(current_date, prev_date):
    current = load_quotes(current_date)
    previous = load_quotes(prev_date)
    if not current or not previous:
        print(f"  数据缺失: current={current is not None}, prev={previous is not None}")
        return
    
    stale_single = []
    for p in products:
        code = p["code"]
        if code not in current:
            continue
        if detect_single_day_stale(current[code], previous.get(code, {})):
            stale_single.append(code)
    
    print(f"  单日陈旧: {len(stale_single)}/{len(products)} 个品种")
    if stale_single:
        print(f"    品种: {', '.join(stale_single)}")

# 测试数据指纹（检测连续多天）
def test_fingerprint_consistency():
    print("\n--- 数据指纹一致性检测（连续3天）---")
    dates = ["20260713", "20260714", "20260715"]
    for p in products:
        code = p["code"]
        fingerprints = []
        for d in dates:
            q = load_quotes(d)
            if q and code in q:
                fingerprints.append(_compute_data_fingerprint(q[code]))
            else:
                fingerprints.append(None)
        
        if all(fp == fingerprints[0] and fp is not None for fp in fingerprints):
            print(f"  🔴 {code} ({p['name']}): 连续3天数据完全相同！")

print("=" * 60)
print("数据守护者 - 历史数据回溯测试")
print("=" * 60)

print("\n--- 7月14日 vs 7月13日 ---")
test_date_pair("20260714", "20260713")

print("\n--- 7月15日 vs 7月14日 ---")
test_date_pair("20260715", "20260714")

print("\n--- 7月15日 vs 7月13日 ---")
test_date_pair("20260715", "20260713")

test_fingerprint_consistency()

print("\n" + "=" * 60)
print("测试完成")
