#!/usr/bin/env python3
"""
期货基本面日报 - 新闻情绪分析模块
接入华尔街见闻API，进行品种级别的情绪分析
"""

import requests
import json
import re
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"

# 品种关键词映射
PRODUCT_KEYWORDS = {
    "PS": ["多晶硅", "硅料", "光伏", "硅片", "隆基", "通威", "大全能源"],
    "RM": ["菜粕", "菜籽", "油菜籽", "菜油", "饲料", "养殖"],
    "PB": ["铅", "沪铅", "蓄电池", "电池回收", "再生铅"],
    "RB": ["螺纹钢", "钢材", "钢铁", "铁矿石", "地产", "基建"],
    "SC": ["原油", "石油", "OPEC", "布伦特", "WTI", "页岩油"],
    "M": ["豆粕", "大豆", "美豆", "南美大豆", "饲料", "养殖", "生猪"],
    "I": ["铁矿石", "铁矿", "巴西", "澳洲", "发运", "港口库存"],
    "CU": ["铜", "沪铜", "铜矿", "精铜", "电网", "新能源铜"],
    "P": ["棕榈油", "马棕", "印尼", "生物柴油", "食用油"],
    "SA": ["纯碱", "玻璃", "光伏玻璃", "浮法玻璃", "远兴能源"],
}


def fetch_wallstreet_news(limit=50, hours_back=24):
    """
    抓取华尔街见闻要闻
    """
    url = "https://api.wallstreetcn.com/apiv1/content/lives"
    params = {
        "channel": "global",
        "limit": limit,
    }
    
    try:
        resp = requests.get(url, params=params, timeout=15)
        if resp.status_code != 200:
            print(f"[WARN] 华尔街见闻API返回 {resp.status_code}")
            return []
        
        data = resp.json()
        if "data" not in data or "items" not in data["data"]:
            return []
        
        items = data["data"]["items"]
        
        # 过滤时间范围
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        filtered_items = []
        
        for item in items:
            display_time = item.get("display_time", "")
            if not display_time:
                continue
            
            try:
                # 尝试解析时间
                item_time = datetime.fromisoformat(display_time.replace("Z", "+00:00"))
                if item_time >= cutoff_time:
                    filtered_items.append(item)
            except:
                # 如果时间解析失败，保留所有
                filtered_items.append(item)
        
        return filtered_items
    except Exception as e:
        print(f"[WARN] 华尔街见闻新闻获取失败: {e}")
        return []


def analyze_sentiment(text):
    """
    简单的情感词典分析
    返回: (sentiment_score, sentiment_label)
    sentiment_score: -1 (极度悲观) 到 +1 (极度乐观)
    """
    positive_words = [
        "上涨", "反弹", "突破", "利好", "强劲", "超预期", "改善", "回升",
        "增长", "扩张", "支撑", "看好", "买入", "增持", "企稳", "回暖",
        "乐观", "积极", "正面", "提升", "增加", "旺盛", "紧张", "短缺",
        "去库存", "供不应求", "景气", "繁荣", "牛市", "走高", "拉升",
        "强势", "涨停", "大涨", "飙升", "创新高", "放量", "资金流入"
    ]
    
    negative_words = [
        "下跌", "回调", "破位", "利空", "疲软", "不及预期", "恶化", "回落",
        "下降", "收缩", "压制", "看空", "卖出", "减持", "承压", "降温",
        "悲观", "消极", "负面", "下滑", "减少", "低迷", "过剩", "累库",
        "去库存缓慢", "供过于求", "衰退", "萧条", "熊市", "走低", "杀跌",
        "弱势", "跌停", "大跌", "暴跌", "创新低", "缩量", "资金流出",
        "风险", "警惕", "谨慎", "担忧", "恐慌", "不确定性"
    ]
    
    text_lower = text.lower()
    
    pos_count = sum(1 for word in positive_words if word in text)
    neg_count = sum(1 for word in negative_words if word in text)
    
    total = pos_count + neg_count
    if total == 0:
        return 0, "中性"
    
    score = (pos_count - neg_count) / total
    
    if score > 0.3:
        return score, "乐观"
    elif score < -0.3:
        return score, "悲观"
    else:
        return score, "中性"


def match_product_news(news_items):
    """
    将新闻与品种匹配，计算每个品种的情绪分数
    返回: {code: {"sentiment": float, "label": str, "news_count": int, "top_news": [str]}}
    """
    results = {}
    
    for code, keywords in PRODUCT_KEYWORDS.items():
        matched_news = []
        sentiments = []
        
        for item in news_items:
            title = item.get("title", "")
            content = item.get("content", "")
            full_text = f"{title} {content}"
            
            # 检查是否包含品种关键词
            if any(kw in full_text for kw in keywords):
                sentiment_score, sentiment_label = analyze_sentiment(full_text)
                matched_news.append({
                    "title": title,
                    "content": content[:200] if content else "",
                    "time": item.get("display_time", ""),
                    "sentiment_score": sentiment_score,
                    "sentiment_label": sentiment_label
                })
                sentiments.append(sentiment_score)
        
        if sentiments:
            avg_sentiment = sum(sentiments) / len(sentiments)
            if avg_sentiment > 0.2:
                label = "乐观"
            elif avg_sentiment < -0.2:
                label = "悲观"
            else:
                label = "中性"
            
            # 取最相关的3条新闻
            top_news = sorted(matched_news, key=lambda x: abs(x["sentiment_score"]), reverse=True)[:3]
            
            results[code] = {
                "sentiment": round(avg_sentiment, 2),
                "label": label,
                "news_count": len(matched_news),
                "top_news": top_news
            }
        else:
            results[code] = {
                "sentiment": 0,
                "label": "中性",
                "news_count": 0,
                "top_news": []
            }
    
    return results


def fetch_and_analyze_news():
    """
    主函数：获取新闻并分析
    """
    print(f"[{datetime.now()}] 开始获取华尔街见闻新闻...")
    
    news_items = fetch_wallstreet_news(limit=50, hours_back=24)
    if not news_items:
        print("[WARN] 未获取到新闻数据")
        return {}
    
    print(f"  获取到 {len(news_items)} 条新闻")
    
    results = match_product_news(news_items)
    
    # 保存结果
    date_str = datetime.now().strftime("%Y%m%d")
    output_file = DATA_DIR / f"news_sentiment_{date_str}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"[{datetime.now()}] 新闻情绪分析完成，已保存: {output_file}")
    
    # 打印摘要
    for code, data in results.items():
        if data["news_count"] > 0:
            print(f"  {code}: 情绪={data['label']}({data['sentiment']:+.2f}), 相关新闻={data['news_count']}条")
    
    return results


if __name__ == "__main__":
    results = fetch_and_analyze_news()
    print(json.dumps(results, ensure_ascii=False, indent=2))
