#!/usr/bin/env python3
"""生成 report_index.json 从现有分析数据"""
import json
import os
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
ANALYSIS_DIR = BASE_DIR / "analysis"
ARCHIVE_DIR = BASE_DIR / "archive"
OUTPUT_DIR = BASE_DIR / "output"

def build_index():
    reports = []
    
    for analysis_file in sorted(ANALYSIS_DIR.glob("analysis_*.json")):
        with open(analysis_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        date_str = analysis_file.stem.replace("analysis_", "")
        date_fmt = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
        filename = f"{date_fmt}.html"
        
        if not (ARCHIVE_DIR / filename).exists():
            continue
        
        # 计算统计
        up_count = sum(1 for d in data if d["quote"]["change_pct"] >= 0)
        down_count = len(data) - up_count
        direction = "涨多跌少" if up_count > down_count else "跌多涨少" if down_count > up_count else "涨跌均衡"
        
        # 最高涨幅
        top_gainer = max(data, key=lambda x: x["quote"]["change_pct"])
        top_gainer_str = f"{top_gainer['name']}({top_gainer['code']}) {'+' if top_gainer['quote']['change_pct'] >= 0 else ''}{top_gainer['quote']['change_pct']:.2f}%"
        
        # 最高评分
        top_score = max(data, key=lambda x: x["score"])
        top_score_str = f"{top_score['name']}({top_score['code']}) {top_score['score']:.1f}分"
        
        # 板块
        sectors = sorted(set(d["sector"] for d in data))
        
        reports.append({
            "date": date_fmt,
            "filename": filename,
            "title": f"期货基本面日报 {date_fmt}",
            "top_gainer": top_gainer_str,
            "top_score": top_score_str,
            "direction": direction,
            "sectors": sectors,
            "up_count": up_count,
            "down_count": down_count
        })
    
    # 按日期倒序
    reports.sort(key=lambda x: x["date"], reverse=True)
    
    index = {
        "version": "v2.0",
        "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "reports": reports
    }
    
    index_file = BASE_DIR / "report_index.json"
    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    
    print(f"[OK] report_index.json 已生成: {index_file}")
    print(f"  共 {len(reports)} 条报告索引")
    return index

if __name__ == "__main__":
    build_index()
