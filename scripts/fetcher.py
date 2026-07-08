#!/usr/bin/env python3
"""
期货基本面日报 - 数据抓取模块
支持大商所、上期所、郑商所、广期所行情数据
"""

import requests
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
CONFIG_PATH = BASE_DIR / "config.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_trade_date():
    """获取当前交易日（如果收盘前，取上一个交易日）"""
    now = datetime.now()
    # 如果今天不是交易日或还未收盘，取上一个交易日
    if now.weekday() >= 5:  # 周六日
        days_back = now.weekday() - 4
        return (now - timedelta(days=days_back)).strftime("%Y%m%d")
    return now.strftime("%Y%m%d")


def fetch_dce_quotes(products):
    """大商所行情"""
    results = {}
    dce_products = [p for p in products if p["exchange"] == "大商所"]
    if not dce_products:
        return results
    
    try:
        # 大商所行情API
        url = "http://www.dce.com.cn/publicweb/1.0/quotesGet.html"
        for prod in dce_products:
            code = prod["code"]
            # 尝试获取主力合约
            params = {"variety": code.lower(), "contract": "all"}
            try:
                resp = requests.get(url, params=params, headers=HEADERS, timeout=10)
                if resp.status_code == 200:
                    # 解析返回数据，取成交量最大的合约
                    data = resp.json()
                    if data and len(data) > 0:
                        main_contract = max(data, key=lambda x: x.get("volume", 0))
                        results[code] = {
                            "close": float(main_contract.get("close", 0)),
                            "change_pct": float(main_contract.get("changePercent", 0)),
                            "volume": int(main_contract.get("volume", 0)),
                            "open_interest": int(main_contract.get("openInterest", 0)),
                            "contract": main_contract.get("contract", ""),
                            "date": get_trade_date()
                        }
            except Exception as e:
                print(f"[WARN] 大商所 {code} 获取失败: {e}")
                continue
    except Exception as e:
        print(f"[WARN] 大商所整体获取失败: {e}")
    
    return results


def fetch_shfe_quotes(products):
    """上期所行情"""
    results = {}
    shfe_products = [p for p in products if p["exchange"] == "上期所"]
    if not shfe_products:
        return results
    
    try:
        # 上期所行情API
        url = "https://www.shfe.com.cn/data/dailydata/kx/kx20260708.dat"
        # 实际上期所API需要动态日期，这里用新浪期货API作为备选
        for prod in shfe_products:
            code = prod["code"]
            # 使用新浪期货API
            sina_code = f"{code.lower()}0" if code != "PB" else "pb0"
            sina_url = f"https://hq.sinajs.cn/list=NF_{sina_code}"
            try:
                resp = requests.get(sina_url, headers={"Referer": "https://finance.sina.com.cn"}, timeout=10)
                if resp.status_code == 200:
                    text = resp.text
                    if "var hq_str_NF" in text:
                        parts = text.split('"')[1].split(",")
                        if len(parts) >= 14:
                            results[code] = {
                                "close": float(parts[7]) if parts[7] else 0,
                                "change_pct": float(parts[10]) if parts[10] else 0,
                                "volume": int(parts[13]) if parts[13] else 0,
                                "open_interest": int(parts[14]) if len(parts) > 14 and parts[14] else 0,
                                "contract": "主力合约",
                                "date": get_trade_date()
                            }
            except Exception as e:
                print(f"[WARN] 上期所 {code} 获取失败: {e}")
                continue
    except Exception as e:
        print(f"[WARN] 上期所整体获取失败: {e}")
    
    return results


def fetch_czce_quotes(products):
    """郑商所行情"""
    results = {}
    czce_products = [p for p in products if p["exchange"] == "郑商所"]
    if not czce_products:
        return results
    
    try:
        for prod in czce_products:
            code = prod["code"]
            # 使用新浪期货API
            sina_code_map = {"RM": "rm0", "SA": "sa0"}
            sina_code = sina_code_map.get(code, code.lower() + "0")
            sina_url = f"https://hq.sinajs.cn/list=NF_{sina_code}"
            try:
                resp = requests.get(sina_url, headers={"Referer": "https://finance.sina.com.cn"}, timeout=10)
                if resp.status_code == 200:
                    text = resp.text
                    if "var hq_str_NF" in text:
                        parts = text.split('"')[1].split(",")
                        if len(parts) >= 14:
                            results[code] = {
                                "close": float(parts[7]) if parts[7] else 0,
                                "change_pct": float(parts[10]) if parts[10] else 0,
                                "volume": int(parts[13]) if parts[13] else 0,
                                "open_interest": int(parts[14]) if len(parts) > 14 and parts[14] else 0,
                                "contract": "主力合约",
                                "date": get_trade_date()
                            }
            except Exception as e:
                print(f"[WARN] 郑商所 {code} 获取失败: {e}")
                continue
    except Exception as e:
        print(f"[WARN] 郑商所整体获取失败: {e}")
    
    return results


def fetch_gfex_quotes(products):
    """广期所行情"""
    results = {}
    gfex_products = [p for p in products if p["exchange"] == "广期所"]
    if not gfex_products:
        return results
    
    try:
        for prod in gfex_products:
            code = prod["code"]
            # 使用新浪期货API
            sina_code = f"{code.lower()}0"
            sina_url = f"https://hq.sinajs.cn/list=NF_{sina_code}"
            try:
                resp = requests.get(sina_url, headers={"Referer": "https://finance.sina.com.cn"}, timeout=10)
                if resp.status_code == 200:
                    text = resp.text
                    if "var hq_str_NF" in text:
                        parts = text.split('"')[1].split(",")
                        if len(parts) >= 14:
                            results[code] = {
                                "close": float(parts[7]) if parts[7] else 0,
                                "change_pct": float(parts[10]) if parts[10] else 0,
                                "volume": int(parts[13]) if parts[13] else 0,
                                "open_interest": int(parts[14]) if len(parts) > 14 and parts[14] else 0,
                                "contract": "主力合约",
                                "date": get_trade_date()
                            }
            except Exception as e:
                print(f"[WARN] 广期所 {code} 获取失败: {e}")
                continue
    except Exception as e:
        print(f"[WARN] 广期所整体获取失败: {e}")
    
    return results


def fetch_ine_quotes(products):
    """上期能源行情（原油等）"""
    results = {}
    ine_products = [p for p in products if p["exchange"] == "上期能源"]
    if not ine_products:
        return results
    
    try:
        for prod in ine_products:
            code = prod["code"]
            # 原油用新浪期货API
            sina_url = f"https://hq.sinajs.cn/list=NF_sc0"
            try:
                resp = requests.get(sina_url, headers={"Referer": "https://finance.sina.com.cn"}, timeout=10)
                if resp.status_code == 200:
                    text = resp.text
                    if "var hq_str_NF" in text:
                        parts = text.split('"')[1].split(",")
                        if len(parts) >= 14:
                            results[code] = {
                                "close": float(parts[7]) if parts[7] else 0,
                                "change_pct": float(parts[10]) if parts[10] else 0,
                                "volume": int(parts[13]) if parts[13] else 0,
                                "open_interest": int(parts[14]) if len(parts) > 14 and parts[14] else 0,
                                "contract": "主力合约",
                                "date": get_trade_date()
                            }
            except Exception as e:
                print(f"[WARN] 上期能源 {code} 获取失败: {e}")
                continue
    except Exception as e:
        print(f"[WARN] 上期能源整体获取失败: {e}")
    
    return results


def fetch_related_stocks():
    """
    抓取关联上市公司股票行情（通过kimi_finance）
    返回: {code: {stocks: [{name, code, close, change_pct, sector_avg_change}]}}
    """
    from analyzer import PRODUCT_KNOWLEDGE
    
    print(f"[{datetime.now()}] 开始抓取关联股票数据...")
    
    # 收集所有关联股票代码
    all_stock_codes = set()
    code_to_stocks = {}  # 期货code -> 关联股票列表
    
    for fut_code, knowledge in PRODUCT_KNOWLEDGE.items():
        stocks = knowledge.get("related_stocks", [])
        if stocks:
            code_to_stocks[fut_code] = stocks
            for s in stocks:
                all_stock_codes.add(s["code"])
    
    if not all_stock_codes:
        print("[INFO] 无关联股票配置，跳过")
        return {}
    
    # 使用kimi_finance的stock_finance_data接口获取实时行情
    # 这里使用腾讯API作为快速实现（同花顺数据通过kimi_finance需要file_path参数）
    stock_results = {}
    
    for fut_code, stocks in code_to_stocks.items():
        stock_list = []
        sector_changes = []
        
        for s in stocks:
            stock_code = s["code"]
            # 使用腾讯API获取股票实时行情
            # 转换代码格式: 601012.SH -> sh601012, 300999.SZ -> sz300999
            if ".SH" in stock_code:
                tencent_code = f"sh{stock_code.replace('.SH', '')}"
            elif ".SZ" in stock_code:
                tencent_code = f"sz{stock_code.replace('.SZ', '')}"
            else:
                continue
            
            try:
                url = f"https://qt.gtimg.cn/q={tencent_code}"
                resp = requests.get(url, timeout=10)
                if resp.status_code == 200:
                    text = resp.text
                    # 解析腾讯行情格式: v_sh601012="名称;今开;昨收;最新;最高;最低;..."
                    if f'v_{tencent_code}="' in text:
                        data_str = text.split('"')[1]
                        parts = data_str.split("~")
                        if len(parts) >= 45:
                            stock_list.append({
                                "name": s["name"],
                                "code": stock_code,
                                "close": float(parts[3]) if parts[3] else 0,
                                "change_pct": float(parts[32]) if parts[32] else 0,
                                "weight": s.get("weight", 0.33)
                            })
                            sector_changes.append(float(parts[32]) if parts[32] else 0)
            except Exception as e:
                print(f"[WARN] 股票 {stock_code} 获取失败: {e}")
                continue
        
        # 计算板块加权平均涨跌幅
        if stock_list and sector_changes:
            weighted_change = sum(
                s["change_pct"] * s["weight"] for s in stock_list
            ) / sum(s["weight"] for s in stock_list)
            
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


def fetch_mock_stocks():
    """生成模拟股票数据（用于测试）"""
    from analyzer import PRODUCT_KNOWLEDGE
    import random
    
    results = {}
    for fut_code, knowledge in PRODUCT_KNOWLEDGE.items():
        stocks = knowledge.get("related_stocks", [])
        if not stocks:
            continue
        
        stock_list = []
        for s in stocks:
            change = round(random.uniform(-3, 4), 2)
            stock_list.append({
                "name": s["name"],
                "code": s["code"],
                "close": round(random.uniform(10, 100), 2),
                "change_pct": change,
                "weight": s.get("weight", 0.33)
            })
        
        weighted_change = sum(s["change_pct"] * s["weight"] for s in stock_list) / sum(s["weight"] for s in stock_list)
        
        results[fut_code] = {
            "stocks": stock_list,
            "sector_avg_change": round(weighted_change, 2),
            "sector_direction": "强势" if weighted_change > 1 else "弱势" if weighted_change < -1 else "震荡"
        }
    
    date_str = get_trade_date()
    output_file = DATA_DIR / f"stocks_{date_str}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    return results


def fetch_all_quotes():
    """抓取所有品种行情"""
    config = load_config()
    products = config["products"]
    
    print(f"[{datetime.now()}] 开始抓取期货行情数据...")
    
    all_results = {}
    all_results.update(fetch_dce_quotes(products))
    all_results.update(fetch_shfe_quotes(products))
    all_results.update(fetch_czce_quotes(products))
    all_results.update(fetch_gfex_quotes(products))
    all_results.update(fetch_ine_quotes(products))
    
    # 保存数据
    date_str = get_trade_date()
    output_file = DATA_DIR / f"quotes_{date_str}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    print(f"[{datetime.now()}] 行情数据已保存: {output_file}")
    print(f"  成功获取 {len(all_results)}/{len(products)} 个品种")
    
    # 抓取关联股票
    fetch_related_stocks()
    
    return all_results


def fetch_mock_data():
    """生成模拟数据（用于测试）"""
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
    
    # 同时生成模拟股票数据
    fetch_mock_stocks()
    
    return results


if __name__ == "__main__":
    # 检查是否有 --mock 参数
    import sys
    if "--mock" in sys.argv:
        data = fetch_mock_data()
    else:
        data = fetch_all_quotes()
    print(json.dumps(data, ensure_ascii=False, indent=2))
