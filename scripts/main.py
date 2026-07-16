#!/usr/bin/env python3
"""
期货基本面日报 - 主控脚本
协调数据抓取 → AI分析 → HTML生成 → Git推送
"""

import sys
import os
from pathlib import Path

# 添加scripts目录到路径
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR / "scripts"))

from fetcher import fetch_all_quotes, fetch_mock_data
from news_analyzer import fetch_and_analyze_news
from macro_data import fetch_macro_data
from analyzer import analyze_all
from generator import generate_html
from pusher import push_all, push_local


def run_pipeline(mock=False, local=False, skip_guardian=False):
    """执行完整流水线"""
    print("=" * 60)
    print("期货基本面日报 - 生成流水线")
    print("=" * 60)
    
    # 1. 数据抓取（期货行情 + 关联股票）
    if mock:
        print("\n[1/6] 使用模拟数据...")
        fetch_mock_data()
    else:
        print("\n[1/6] 抓取行情数据...")
        quotes = fetch_all_quotes()
    
    # 1.5 数据质量检查（守护者）
    if not mock and not skip_guardian:
        print("\n[1.5/6] 数据质量检查...")
        try:
            import sys
            from pathlib import Path
            BASE_DIR = Path(__file__).parent.parent
            sys.path.insert(0, str(BASE_DIR / "scripts"))
            from data_guardian import run_guardian_check, load_config
            config = load_config()
            products = config["products"]
            report = run_guardian_check(quotes, products)
            summary = report.get("summary", {})
            total = summary.get("total", 10)
            healthy = summary.get("healthy", 0)
            stale = summary.get("stale_single", 0)
            mock_cnt = summary.get("mock_fallback", 0)
            
            print(f"  数据健康度: {healthy}/{total}")
            
            # 如果超过70%数据异常，中止流水线
            bad_ratio = (stale + mock_cnt) / total if total else 0
            if bad_ratio >= 0.7:
                print(f"\n🚨 CRITICAL: {bad_ratio*100:.0f}% 品种数据异常，中止流水线")
                print("  请检查数据源后再试。")
                return
            elif bad_ratio >= 0.5:
                print(f"\n⚠️ WARNING: {bad_ratio*100:.0f}% 品种数据异常，继续但请注意")
        except Exception as e:
            print(f"[WARN] 数据质量检查失败: {e}")
    
    # 2. 新闻情绪分析
    print("\n[2/6] 抓取新闻舆情...")
    try:
        fetch_and_analyze_news()
    except Exception as e:
        print(f"[WARN] 新闻分析失败: {e}")
    
    # 3. 宏观数据
    print("\n[3/6] 抓取宏观数据...")
    try:
        fetch_macro_data()
    except Exception as e:
        print(f"[WARN] 宏观数据获取失败: {e}")
    
    # 4. AI分析
    print("\n[4/6] 执行AI分析...")
    analyze_all()
    
    # 5. HTML生成
    print("\n[5/6] 生成HTML报告...")
    generate_html()
    
    # 6. 推送报告
    print("\n[6/6] 推送报告...")
    if local:
        push_local()
    else:
        push_all()
    
    print("\n" + "=" * 60)
    print("✅ 流水线执行完毕")
    print("=" * 60)


if __name__ == "__main__":
    mock_mode = "--mock" in sys.argv
    local_mode = "--local" in sys.argv
    skip_guardian = "--skip-guardian" in sys.argv
    
    run_pipeline(mock=mock_mode, local=local_mode, skip_guardian=skip_guardian)
