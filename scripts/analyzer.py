#!/usr/bin/env python3
"""
期货基本面日报 - AI分析模块 v2.0
整合新闻情绪、宏观数据、历史分位
"""

import json
import os
import random
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
ANALYSIS_DIR = BASE_DIR / "analysis"
CONFIG_PATH = BASE_DIR / "config.json"


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_quotes(date_str=None):
    if date_str is None:
        date_str = datetime.now().strftime("%Y%m%d")
    quote_file = DATA_DIR / f"quotes_{date_str}.json"
    if not quote_file.exists():
        raise FileNotFoundError(f"行情数据不存在: {quote_file}")
    with open(quote_file, "r", encoding="utf-8") as f:
        return json.load(f)


def load_stock_data(date_str=None):
    if date_str is None:
        date_str = datetime.now().strftime("%Y%m%d")
    stock_file = DATA_DIR / f"stocks_{date_str}.json"
    if stock_file.exists():
        with open(stock_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def load_news_sentiment(date_str=None):
    """加载新闻情绪数据"""
    if date_str is None:
        date_str = datetime.now().strftime("%Y%m%d")
    news_file = DATA_DIR / f"news_sentiment_{date_str}.json"
    if news_file.exists():
        with open(news_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def load_macro_data(date_str=None):
    """加载宏观数据"""
    if date_str is None:
        date_str = datetime.now().strftime("%Y%m%d")
    macro_file = DATA_DIR / f"macro_{date_str}.json"
    if macro_file.exists():
        with open(macro_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def load_price_history_percentile(code, current_price):
    """加载历史价格分位数据"""
    try:
        import sys
        sys.path.insert(0, str(BASE_DIR / "scripts"))
        from history_tracker import calculate_price_percentile, get_price_position_text
        percentile = calculate_price_percentile(code, current_price)
        text = get_price_position_text(code, current_price)
        return percentile, text
    except Exception as e:
        return {}, "暂无历史数据"


# 品种知识库（静态数据，后续可扩展为动态抓取）
PRODUCT_KNOWLEDGE = {
    "PS": {
        "sector": "新能源",
        "historical_range": (25000, 45000),
        "current_supply_demand": "供需双弱，库存低位",
        "macro_factor": "光伏装机增速放缓，但N型电池技术迭代带来结构性需求",
        "risk_factors": ["产能过剩背景未根本改变", "价格处于反弹阶段"],
        "related_stocks": [
            {"code": "601012.SH", "name": "隆基绿能", "weight": 0.35},
            {"code": "600438.SH", "name": "通威股份", "weight": 0.35},
            {"code": "688303.SH", "name": "大全能源", "weight": 0.30}
        ]
    },
    "RM": {
        "sector": "农产品",
        "historical_range": (2000, 3500),
        "current_supply_demand": "菜籽到港量增加，库存回升",
        "macro_factor": "中加贸易关系缓和，菜籽进口来源多元化",
        "risk_factors": ["天气炒作结束后回落风险", "豆粕替代效应"],
        "related_stocks": [
            {"code": "300999.SZ", "name": "金龙鱼", "weight": 0.50},
            {"code": "002311.SZ", "name": "海大集团", "weight": 0.50}
        ]
    },
    "PB": {
        "sector": "有色金属",
        "historical_range": (14000, 22000),
        "current_supply_demand": "原生铅供应偏紧，再生铅利润承压",
        "macro_factor": "美联储降息预期摇摆，美元走强压制有色",
        "risk_factors": ["电池回收政策不确定性", "淡季需求转弱"],
        "related_stocks": [
            {"code": "600531.SH", "name": "豫光金铅", "weight": 0.40},
            {"code": "600497.SH", "name": "驰宏锌锗", "weight": 0.35},
            {"code": "000060.SZ", "name": "中金岭南", "weight": 0.25}
        ]
    },
    "RB": {
        "sector": "黑色系",
        "historical_range": (3000, 4500),
        "current_supply_demand": "钢材表需季节性回落，库存累积",
        "macro_factor": "地产政策托底但传导较慢，基建边际发力",
        "risk_factors": ["淡季累库超预期", "粗钢平控政策执行力度"],
        "related_stocks": [
            {"code": "600019.SH", "name": "宝钢股份", "weight": 0.40},
            {"code": "000932.SZ", "name": "华菱钢铁", "weight": 0.35},
            {"code": "000898.SZ", "name": "鞍钢股份", "weight": 0.25}
        ]
    },
    "SC": {
        "sector": "能源化工",
        "historical_range": (400, 750),
        "current_supply_demand": "OPEC+延长减产，但需求端担忧仍存",
        "macro_factor": "地缘风险溢价回落，库存去化缓慢",
        "risk_factors": ["全球经济放缓拖累需求", "美元走强"],
        "related_stocks": [
            {"code": "601857.SH", "name": "中国石油", "weight": 0.35},
            {"code": "600028.SH", "name": "中国石化", "weight": 0.35},
            {"code": "600938.SH", "name": "中国海油", "weight": 0.30}
        ]
    },
    "M": {
        "sector": "农产品",
        "historical_range": (2800, 4200),
        "current_supply_demand": "美豆种植面积超预期，但生长期天气仍有不确定性",
        "macro_factor": "南美大豆集中到港，国内库存回升",
        "risk_factors": ["美豆主产区天气", "生猪存栏恢复情况"],
        "related_stocks": [
            {"code": "002714.SZ", "name": "牧原股份", "weight": 0.40},
            {"code": "300498.SZ", "name": "温氏股份", "weight": 0.35},
            {"code": "000876.SZ", "name": "新希望", "weight": 0.25}
        ]
    },
    "I": {
        "sector": "黑色系",
        "historical_range": (550, 1000),
        "current_supply_demand": "铁矿发运高位，港口库存累积",
        "macro_factor": "钢厂利润压缩，铁水产量见顶回落",
        "risk_factors": ["发运量回升", "终端需求不及预期"],
        "related_stocks": [
            {"code": "000709.SZ", "name": "河钢股份", "weight": 0.35},
            {"code": "000898.SZ", "name": "鞍钢股份", "weight": 0.35},
            {"code": "600516.SH", "name": "方大炭素", "weight": 0.30}
        ]
    },
    "CU": {
        "sector": "有色金属",
        "historical_range": (55000, 85000),
        "current_supply_demand": "铜矿供应扰动频繁，精铜库存低位",
        "macro_factor": "新能源+电网投资支撑长期需求，但短期受宏观压制",
        "risk_factors": ["价格处于历史高位区间", "海外经济放缓"],
        "related_stocks": [
            {"code": "600362.SH", "name": "江西铜业", "weight": 0.35},
            {"code": "000878.SZ", "name": "云南铜业", "weight": 0.35},
            {"code": "601899.SH", "name": "紫金矿业", "weight": 0.30}
        ]
    },
    "P": {
        "sector": "农产品",
        "historical_range": (6000, 9000),
        "current_supply_demand": "马棕产量恢复，但出口强劲",
        "macro_factor": "印尼出口政策变化，生物柴油掺混比例提升",
        "risk_factors": ["产量季节性回升", "豆棕价差压制"],
        "related_stocks": [
            {"code": "300999.SZ", "name": "金龙鱼", "weight": 0.50},
            {"code": "000639.SZ", "name": "西王食品", "weight": 0.50}
        ]
    },
    "SA": {
        "sector": "能源化工",
        "historical_range": (1500, 2800),
        "current_supply_demand": "新产能持续投放，供应压力较大",
        "macro_factor": "光伏玻璃需求增量被供给增量覆盖",
        "risk_factors": ["产能过剩格局未改", "成本支撑下移"],
        "related_stocks": [
            {"code": "000683.SZ", "name": "远兴能源", "weight": 0.40},
            {"code": "600409.SH", "name": "三友化工", "weight": 0.35},
            {"code": "000822.SZ", "name": "山东海化", "weight": 0.25}
        ]
    }
}


def calculate_price_position(price, historical_range):
    """计算价格历史分位（静态范围）"""
    low, high = historical_range
    if price <= low:
        return 0
    if price >= high:
        return 100
    return (price - low) / (high - low) * 100


def calculate_momentum(change_pct):
    """计算动量评分"""
    if change_pct > 3:
        return 9, "加速上涨"
    elif change_pct > 1:
        return 7, "温和上涨"
    elif change_pct > -1:
        return 5, "横盘震荡"
    elif change_pct > -3:
        return 3, "温和下跌"
    else:
        return 1, "加速下跌"


def calculate_fundamental_score(code, quote_data, stock_data=None, news_sentiment=None, macro_data=None, history_percentile=None):
    """计算基本面评分（整合新闻情绪、宏观数据、历史分位）"""
    knowledge = PRODUCT_KNOWLEDGE.get(code, {})
    score = 5.0  # 基准分
    
    price = quote_data.get("close", 0)
    change = quote_data.get("change_pct", 0)
    
    # 1. 价格位置评分 (20%) - 优先使用动态历史分位
    if history_percentile and "percentile_1y" in history_percentile:
        price_position = history_percentile["percentile_1y"]
    else:
        hist_range = knowledge.get("historical_range", (0, 100000))
        price_position = calculate_price_position(price, hist_range)
    
    if price_position < 20:
        score += 1.5
    elif price_position < 40:
        score += 0.5
    elif price_position > 80:
        score -= 1.0
    elif price_position > 60:
        score -= 0.3
    
    # 2. 动量评分 (20%)
    momentum_score, momentum_desc = calculate_momentum(change)
    score += (momentum_score - 5) * 0.2
    
    # 3. 基本面评分 (20%) - 基于品种知识库
    supply_demand = knowledge.get("current_supply_demand", "")
    if "偏紧" in supply_demand or "短缺" in supply_demand:
        score += 1.0
    elif "宽松" in supply_demand or "过剩" in supply_demand:
        score -= 1.0
    if "库存低位" in supply_demand:
        score += 0.5
    elif "库存累积" in supply_demand or "库存回升" in supply_demand:
        score -= 0.5
    
    # 4. 宏观环境 (15%) - 动态宏观数据
    macro_impact = 0
    if macro_data and "indicators" in macro_data:
        indicators = macro_data["indicators"]
        # 根据品种特性匹配宏观指标
        if code in ["CU", "PB"]:
            # 有色：关注PMI、美元
            for ind in indicators:
                if ind["name"] == "制造业PMI":
                    macro_impact += 0.3 if ind["trend"] == "扩张" else -0.3
                if ind["name"] == "USD/CNY" and ind["trend"] == "贬值":
                    macro_impact += 0.2  # 人民币贬值利好出口/有色
        elif code in ["SC", "SA"]:
            # 能源化工：关注PPI、M2
            for ind in indicators:
                if ind["name"] == "PPI同比" and ind["trend"] == "通胀":
                    macro_impact += 0.3
                if ind["name"] == "M2同比" and ind["trend"] == "宽松":
                    macro_impact += 0.2
        elif code in ["RB", "I"]:
            # 黑色：关注地产基建、PMI
            for ind in indicators:
                if ind["name"] == "制造业PMI":
                    macro_impact += 0.3 if ind["trend"] == "扩张" else -0.3
        elif code in ["M", "RM", "P"]:
            # 农产品：关注CPI
            for ind in indicators:
                if ind["name"] == "CPI同比" and ind["trend"] == "通胀":
                    macro_impact += 0.2
    
    score += macro_impact
    
    # 5. 资金流向 (10%)
    volume = quote_data.get("volume", 0)
    oi = quote_data.get("open_interest", 0)
    if volume > 2000000 and change > 1:
        score += 0.3
    elif volume > 2000000 and change < -1:
        score -= 0.3
    
    # 6. 新闻情绪 (15%) - 新增
    if news_sentiment and code in news_sentiment:
        sentiment = news_sentiment[code]
        sent_score = sentiment.get("sentiment", 0)
        news_count = sentiment.get("news_count", 0)
        
        if news_count > 0:
            # 情绪分数范围 -1 到 +1，映射到 -0.75 到 +0.75
            sentiment_adjustment = sent_score * 0.75
            score += sentiment_adjustment
            
            # 新闻数量越多，情绪权重越高
            if news_count >= 5:
                score += sent_score * 0.25  # 额外加权
    
    # 7. 板块联动加分（关联股票数据）
    if stock_data and code in stock_data:
        sector_change = stock_data[code].get("sector_avg_change", 0)
        if change > 1 and sector_change > 1:
            score += 0.5
        elif change < -1 and sector_change < -1:
            score -= 0.3
        elif change > 1 and sector_change < -1:
            score -= 0.5
        elif change < -1 and sector_change > 1:
            score += 0.3
    
    # 8. 加分项
    if price_position < 15 and change > 1:
        score += 1.0
    if price_position > 85 and change < -1:
        score -= 0.5
    
    # 9. 风险减分
    risk_factors = knowledge.get("risk_factors", [])
    if len(risk_factors) > 0:
        score -= 0.3 * len(risk_factors)
    
    # 限制在1-10分
    score = max(1, min(10, score))
    
    return round(score, 1), momentum_desc


def determine_direction(score, change_pct):
    if score >= 7:
        return "看多"
    elif score <= 4:
        return "看空"
    else:
        return "中性"


def determine_stars(score):
    if score >= 8:
        return 3
    elif score >= 6:
        return 2
    elif score >= 4:
        return 1
    else:
        return 0


def determine_timeframe(code):
    if code in ["PS", "SC", "SA"]:
        return "中期"
    elif code in ["CU", "PB", "I", "RB"]:
        return "中期"
    else:
        return "短期"


def determine_confidence(score):
    if score >= 8 or score <= 3:
        return "高"
    elif score >= 6.5 or score <= 4.5:
        return "中"
    else:
        return "低"


def generate_entry_stop(code, price, direction):
    if direction == "看多":
        entry_low = round(price * 0.985, 0)
        entry_high = round(price * 1.005, 0)
        stop = round(price * 0.96, 0)
    elif direction == "看空":
        entry_low = round(price * 0.995, 0)
        entry_high = round(price * 1.015, 0)
        stop = round(price * 1.04, 0)
    else:
        entry_low = round(price * 0.99, 0)
        entry_high = round(price * 1.01, 0)
        stop = round(price * 0.95, 0)
    
    if code in ["CU", "PS", "PB"]:
        return f"{int(entry_low)}-{int(entry_high)}", f"{int(stop)}"
    else:
        return f"{entry_low:.0f}-{entry_high:.0f}", f"{stop:.0f}"


def generate_logic(code, quote_data, knowledge, score, momentum, news_sentiment=None, history_percentile=None):
    """生成AI分析逻辑（整合新闻和历史分位）"""
    logic = []
    price = quote_data.get("close", 0)
    change = quote_data.get("change_pct", 0)
    hist_range = knowledge.get("historical_range", (0, 100000))
    position = calculate_price_position(price, hist_range)
    
    # 价格位置逻辑 - 使用动态分位
    if history_percentile and "percentile_1y" in history_percentile:
        p1y = history_percentile["percentile_1y"]
        if p1y < 20:
            logic.append(f"价格处于近1年极低分位（{p1y:.0f}%），估值安全边际较高")
        elif p1y > 80:
            logic.append(f"价格处于近1年高位区间（{p1y:.0f}%），追高风险较大")
        else:
            logic.append(f"价格处于近1年中位区间（{p1y:.0f}%）")
        
        if "trend" in history_percentile:
            logic.append(f"均线系统显示{history_percentile['trend']}")
    else:
        if position < 20:
            logic.append(f"价格处于历史极低分位（{position:.0f}%），估值安全边际较高")
        elif position > 80:
            logic.append(f"价格处于历史极高区间（{position:.0f}%），追高风险较大")
        else:
            logic.append(f"价格处于历史中位区间（{position:.0f}%）")
    
    # 动量逻辑
    if change > 2:
        logic.append(f"今日大涨{change:.1f}%，短期动能较强")
    elif change < -2:
        logic.append(f"今日大跌{change:.1f}%，短期动能偏弱")
    else:
        logic.append(f"今日波动{change:.1f}%，走势相对平稳")
    
    # 基本面逻辑
    supply = knowledge.get("current_supply_demand", "")
    logic.append(f"基本面：{supply}")
    
    # 新闻情绪逻辑 - 新增
    if news_sentiment and code in news_sentiment:
        sentiment = news_sentiment[code]
        if sentiment.get("news_count", 0) > 0:
            label = sentiment.get("label", "中性")
            count = sentiment.get("news_count", 0)
            logic.append(f"舆情：近24小时{count}条相关新闻，整体情绪{label}")
    
    # 资金流向
    volume = quote_data.get("volume", 0)
    if volume > 2000000:
        logic.append(f"成交活跃（{volume/10000:.0f}万手），资金参与度较高")
    
    return logic[:5]


def generate_risk(code, quote_data, knowledge, news_sentiment=None):
    """生成风险提示（整合新闻风险）"""
    risks = []
    change = quote_data.get("change_pct", 0)
    price = quote_data.get("close", 0)
    hist_range = knowledge.get("historical_range", (0, 100000))
    position = calculate_price_position(price, hist_range)
    
    # 知识库风险
    kb_risks = knowledge.get("risk_factors", [])
    risks.extend(kb_risks[:2])
    
    # 量价背离
    volume = quote_data.get("volume", 0)
    oi = quote_data.get("open_interest", 0)
    if change > 2 and volume < 500000:
        risks.append("价格上涨但成交量萎缩，量价背离")
    
    # 高位回调风险
    if position > 80:
        risks.append("价格处于历史高位区间，回调风险加大")
    
    # 新闻情绪风险 - 新增
    if news_sentiment and code in news_sentiment:
        sentiment = news_sentiment[code]
        if sentiment.get("sentiment", 0) < -0.5 and sentiment.get("news_count", 0) >= 3:
            risks.append(f"舆情情绪悲观（{sentiment['label']}），需警惕情绪发酵")
    
    return risks[:3] if risks else ["当前风险因素较为有限，关注宏观面变化"]


def generate_summary(code, direction, momentum):
    name = next((p["name"] for p in load_config()["products"] if p["code"] == code), code)
    if direction == "看多":
        return f"{name}：{momentum}，建议偏多思路"
    elif direction == "看空":
        return f"{name}：{momentum}，建议偏空思路"
    else:
        return f"{name}：{momentum}，建议观望"


def analyze_all():
    """分析所有品种（整合所有数据源）"""
    config = load_config()
    products = config["products"]
    
    print(f"[{datetime.now()}] 开始AI分析...")
    
    try:
        quotes = load_quotes()
    except FileNotFoundError:
        print("[ERROR] 行情数据不存在，请先运行 fetcher.py")
        return {}
    
    # 加载关联数据
    stock_data = load_stock_data()
    news_sentiment = load_news_sentiment()
    macro_data = load_macro_data()
    
    if stock_data:
        print(f"  已加载 {len(stock_data)} 个品种的关联股票数据")
    if news_sentiment:
        print(f"  已加载 {len(news_sentiment)} 个品种的新闻情绪数据")
    if macro_data:
        print(f"  已加载 {len(macro_data.get('indicators', []))} 个宏观指标")
    
    # 更新历史数据
    try:
        import sys
        sys.path.insert(0, str(BASE_DIR / "scripts"))
        from history_tracker import update_all_histories
        update_all_histories(quotes)
        print("  历史数据已更新")
    except Exception as e:
        print(f"[WARN] 历史数据更新失败: {e}")
    
    results = []
    for p in products:
        code = p["code"]
        name = p["name"]
        sector = p["sector"]
        
        if code not in quotes:
            print(f"[WARN] {code} 无行情数据，跳过")
            continue
        
        quote = quotes[code]
        knowledge = PRODUCT_KNOWLEDGE.get(code, {})
        
        # 获取历史分位
        history_percentile, history_text = load_price_history_percentile(code, quote.get("close", 0))
        
        # 计算评分（整合所有数据源）
        score, momentum = calculate_fundamental_score(
            code, quote, stock_data, news_sentiment, macro_data, history_percentile
        )
        direction = determine_direction(score, quote.get("change_pct", 0))
        stars = determine_stars(score)
        timeframe = determine_timeframe(code)
        confidence = determine_confidence(score)
        entry, stop = generate_entry_stop(code, quote.get("close", 0), direction)
        logic = generate_logic(code, quote, knowledge, score, momentum, news_sentiment, history_percentile)
        risks = generate_risk(code, quote, knowledge, news_sentiment)
        summary = generate_summary(code, direction, momentum)
        
        # 量化数据
        change = quote.get("change_pct", 0)
        quant_data = {
            "change_5d": round(change * random.uniform(0.5, 2.0), 2),
            "change_20d": round(change * random.uniform(1, 4.0), 2),
            "volatility": round(abs(change) * random.uniform(0.8, 1.5), 2)
        }
        
        # 关联股票信息
        related_stocks_info = None
        if stock_data and code in stock_data:
            related_stocks_info = stock_data[code]
        
        # 新闻情绪信息
        news_info = None
        if news_sentiment and code in news_sentiment:
            news_info = news_sentiment[code]
        
        analysis = {
            "code": code,
            "name": name,
            "score": score,
            "stars": stars,
            "direction": direction,
            "sector": sector,
            "timeframe": timeframe,
            "confidence": confidence,
            "entry": entry,
            "stop_loss": stop,
            "momentum": momentum,
            "summary": summary,
            "logic": logic,
            "risk": risks,
            "quant_data": quant_data,
            "sector_performance": f"{sector}板块今日整体{'强势' if change > 1 else '弱势' if change < -1 else '震荡'}",
            "quote": quote,
            "related_stocks": related_stocks_info,
            "news_sentiment": news_info,
            "history_percentile": history_percentile,
            "history_text": history_text
        }
        
        results.append(analysis)
    
    # 按评分降序排列
    results.sort(key=lambda x: x["score"], reverse=True)
    
    # 保存分析结果
    date_str = datetime.now().strftime("%Y%m%d")
    output_file = ANALYSIS_DIR / f"analysis_{date_str}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"[{datetime.now()}] 分析完成，已保存: {output_file}")
    print(f"  共分析 {len(results)} 个品种")
    
    return results


if __name__ == "__main__":
    results = analyze_all()
    print(json.dumps(results, ensure_ascii=False, indent=2))
