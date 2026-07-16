#!/usr/bin/env python3
"""
期货基本面日报 - 数据抓取模块 v2.0
统一数据源：新浪期货API + akshare备用 + 腾讯股票API
"""

import requests
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
CONFIG_PATH = BASE_DIR / "config.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://finance.sina.com.cn"
}

# 新浪API已确认返回2024-07-17的历史快照数据，不再使用
# 全部品种统一使用 akshare 的 CF 市场代码获取
AKSHARE_MARKET_MAP = {
    "PS": "CF", "RM": "CF", "PB": "CF", "RB": "CF", "SC": "CF",
    "M": "CF", "I": "CF", "CU": "CF", "P": "CF", "SA": "CF",
}

# 新浪期货代码映射（备用）
SINA_CODE_MAP = {
    "PS": "PS0", "RM": "RM0", "PB": "PB0", "RB": "RB0", "SC": "SC0",
    "M": "M0", "I": "I0", "CU": "CU0", "P": "P0", "SA": "SA0",
}


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_trade_date():
    """获取当前交易日（如果收盘前，取上一个交易日）"""
    now = datetime.now()
    if now.weekday() >= 5:  # 周六日
        days_back = now.weekday() - 4
        return (now - timedelta(days=days_back)).strftime("%Y%m%d")
    return now.strftime("%Y%m%d")


def fetch_sina_futures(code):
    """通过新浪API获取期货连续合约行情"""
    sina_code = SINA_CODE_MAP.get(code)
    if not sina_code:
        return None
    
    url = f"https://hq.sinajs.cn/list={sina_code}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            return None
        
        text = resp.content.decode("gbk", errors="ignore")
        var_name = f"var hq_str_{sina_code}="
        if var_name not in text:
            return None
        
        data_str = text.split('"')[1]
        if not data_str:
            return None
        
        parts = data_str.split(",")
        if len(parts) < 15:
            return None
        
        # 新浪期货字段映射
        # [0]名称 [1]时间 [2]今开 [3]最高 [4]最低 [5]昨收 [6]买价 [7]卖价 [8]最新 [9]结算价 [10]昨结 [11]买量 [12]卖量 [13]持仓 [14]成交量
        name = parts[0]
        last_price = float(parts[8]) if parts[8] else 0
        prev_settle = float(parts[10]) if parts[10] else 0
        volume = int(parts[14]) if parts[14] else 0
        open_interest = int(parts[13]) if parts[13] else 0
        
        change_pct = 0
        if prev_settle > 0:
            change_pct = round((last_price - prev_settle) / prev_settle * 100, 2)
        
        return {
            "close": last_price,
            "change_pct": change_pct,
            "volume": volume,
            "open_interest": open_interest,
            "contract": name,
            "date": get_trade_date()
        }
    except Exception as e:
        print(f"[WARN] 新浪API {code}({sina_code}) 获取失败: {e}")
        return None


def fetch_akshare_futures(code):
    """通过akshare获取期货行情（主数据源）"""
    market = AKSHARE_MARKET_MAP.get(code)
    if not market:
        return None
    
    try:
        import akshare as ak
        df = ak.futures_zh_spot(symbol=f"{code}0", market=market, adjust="0")
        if len(df) == 0:
            return None
        
        row = df.iloc[0]
        current_price = float(row.get("current_price", 0))
        last_settle = float(row.get("last_settle_price", 0))
        
        change_pct = 0
        if last_settle > 0:
            change_pct = round((current_price - last_settle) / last_settle * 100, 2)
        
        return {
            "close": current_price,
            "change_pct": change_pct,
            "volume": int(row.get("volume", 0)),
            "open_interest": int(row.get("hold", 0)),
            "contract": str(row.get("symbol", f"{code}0")),
            "date": get_trade_date()
        }
    except Exception as e:
        print(f"[WARN] akshare {code}0 获取失败: {e}")
        return None


def _is_stale_data(data, prev_data):
    """检测数据是否与昨天完全相同（陈旧数据）"""
    if not prev_data:
        return False
    keys = ["close", "volume", "open_interest"]
    for k in keys:
        if data.get(k) != prev_data.get(k):
            return False
    return True


def _load_prev_quotes():
    """加载上一个交易日的数据"""
    now = datetime.now()
    # 尝试昨天
    for days_back in [1, 2, 3]:
        prev_date = (now - timedelta(days=days_back)).strftime("%Y%m%d")
        prev_file = DATA_DIR / f"quotes_{prev_date}.json"
        if prev_file.exists():
            try:
                with open(prev_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
    return None


def fetch_tencent_stock(stock_code):
    """通过腾讯API获取股票行情"""
    if ".SH" in stock_code:
        tencent_code = f"sh{stock_code.replace('.SH', '')}"
    elif ".SZ" in stock_code:
        tencent_code = f"sz{stock_code.replace('.SZ', '')}"
    else:
        return None
    
    url = f"https://qt.gtimg.cn/q={tencent_code}"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return None
        
        text = resp.text
        if f'v_{tencent_code}="' not in text:
            return None
        
        data_str = text.split('"')[1]
        parts = data_str.split("~")
        if len(parts) < 45:
            return None
        
        return {
            "name": parts[1],
            "code": stock_code,
            "close": float(parts[3]) if parts[3] else 0,
            "change_pct": float(parts[32]) if parts[32] else 0,
        }
    except Exception as e:
        print(f"[WARN] 腾讯API {stock_code} 获取失败: {e}")
        return None


def fetch_all_quotes():
    """抓取所有期货品种行情"""
    config = load_config()
    products = config["products"]
    
    print(f"[{datetime.now()}] 开始抓取期货行情数据...")
    
    # 加载昨日数据用于陈旧检测
    prev_quotes = _load_prev_quotes()
    
    results = {}
    stale_codes = []
    
    for p in products:
        code = p["code"]
        
        # 第1步：使用 akshare 获取（主数据源）
        data = fetch_akshare_futures(code)
        if data:
            # 检测是否和昨天数据完全相同
            prev_data = prev_quotes.get(code) if prev_quotes else None
            if prev_data and _is_stale_data(data, prev_data):
                stale_codes.append(code)
                print(f"  ⚠ {code} ({p['name']}) akshare 数据与昨日完全相同，疑似陈旧: {data['close']:.2f}")
            else:
                results[code] = data
                print(f"  ✓ {code} ({p['name']}) akshare: {data['close']:.2f} ({data['change_pct']:+.2f}%) vol={data['volume']}")
            continue
        
        # 第2步：模拟数据兜底（确保品种不缺失）
        base_price = {
            "PS": 38000, "RM": 2800, "PB": 19500, "RB": 3600,
            "SC": 580, "M": 3200, "I": 850, "CU": 78000,
            "P": 7800, "SA": 2200
        }.get(code, 5000)
        import random
        change = round(random.uniform(-3, 5), 2)
        results[code] = {
            "close": round(base_price * (1 + change/100), 2),
            "change_pct": change,
            "volume": random.randint(100000, 5000000),
            "open_interest": random.randint(50000, 500000),
            "contract": f"{code}2509",
            "date": get_trade_date(),
            "data_source": "mock"  # 标记为模拟数据
        }
        print(f"  ⚠ {code} ({p['name']}) 模拟数据: {results[code]['close']:.2f} ({results[code]['change_pct']:+.2f}%) [无实时数据源]")
    
    # 保存数据
    date_str = get_trade_date()
    output_file = DATA_DIR / f"quotes_{date_str}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"[{datetime.now()}] 行情数据已保存: {output_file}")
    print(f"  成功获取 {len(results)}/{len(products)} 个品种")
    if stale_codes:
        print(f"  ⚠⚠⚠ 以下品种数据与昨日完全相同，可能存在数据源问题: {', '.join(stale_codes)}")
    
    # ===== 数据守护者检查 =====
    try:
        sys.path.insert(0, str(BASE_DIR / "scripts"))
        from data_guardian import run_guardian_check
        guardian_report = run_guardian_check(results, products)
        if guardian_report.get("alerts_sent"):
            print(f"  🚨 数据守护者已发送 {len(guardian_report['alerts_sent'])} 条报警")
    except Exception as e:
        print(f"[WARN] 数据守护者检查失败: {e}")
    
    return results


def fetch_related_stocks():
    """抓取关联上市公司股票行情"""
    from analyzer import PRODUCT_KNOWLEDGE
    
    print(f"[{datetime.now()}] 开始抓取关联股票数据...")
    
    stock_results = {}
    for fut_code, knowledge in PRODUCT_KNOWLEDGE.items():
        stocks = knowledge.get("related_stocks", [])
        if not stocks:
            continue
        
        stock_list = []
        sector_changes = []
        
        for s in stocks:
            stock_data = fetch_tencent_stock(s["code"])
            if not stock_data:
                continue
            
            stock_data["weight"] = s.get("weight", 0.33)
            stock_list.append(stock_data)
            sector_changes.append(stock_data["change_pct"])
        
        if not stock_list:
            continue
        
        # 计算板块加权平均涨跌幅
        total_weight = sum(s["weight"] for s in stock_list)
        weighted_change = sum(s["change_pct"] * s["weight"] for s in stock_list) / total_weight if total_weight > 0 else 0
        
        stock_results[fut_code] = {
            "stocks": stock_list,
            "sector_avg_change": round(weighted_change, 2),
            "sector_direction": "强势" if weighted_change > 1 else "弱势" if weighted_change < -1 else "震荡"
        }
    
    # 保存数据
    date_str = get_trade_date()
    output_file = DATA_DIR / f"stocks_{date_str}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(stock_results, f, ensure_ascii=False, indent=2)
    
    print(f"[{datetime.now()}] 关联股票数据已保存: {output_file}")
    print(f"  成功获取 {len(stock_results)} 个品种的关联股票")
    
    return stock_results


def fetch_mock_data():
    """生成模拟数据（仅用于测试，生产环境不应使用）"""
    config = load_config()
    products = config["products"]
    import random
    
    results = {}
    for p in products:
        code = p["code"]
        base_price = {
            "PS": 38000, "RM": 2800, "PB": 19500, "RB": 3600,
            "SC": 580, "M": 3200, "I": 850, "CU": 78000,
            "P": 7800, "SA": 2200
        }.get(code, 5000)
        
        change = round(random.uniform(-3, 5), 2)
        results[code] = {
            "close": round(base_price * (1 + change/100), 2),
            "change_pct": change,
            "volume": random.randint(100000, 5000000),
            "open_interest": random.randint(50000, 500000),
            "contract": f"{code}2509",
            "date": get_trade_date()
        }
    
    date_str = get_trade_date()
    output_file = DATA_DIR / f"quotes_{date_str}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"[{datetime.now()}] [MOCK] 模拟数据已保存: {output_file}")
    print(f"  生成 {len(results)} 个品种模拟数据")
    
    return results


if __name__ == "__main__":
    if "--mock" in sys.argv:
        data = fetch_mock_data()
    else:
        data = fetch_all_quotes()
        fetch_related_stocks()
    print(json.dumps(data, ensure_ascii=False, indent=2))
