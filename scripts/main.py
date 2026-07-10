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
from analyzer import analyze_all
from generator import generate_html
from pusher import push_all, push_local


def run_pipeline(mock=False, local=False):
    """执行完整流水线"""
    print("=" * 60)
    print("期货基本面日报 - 生成流水线")
    print("=" * 60)
    
    # 1. 数据抓取
    if mock:
        print("\n[1/4] 使用模拟数据...")
        fetch_mock_data()
    else:
        print("\n[1/4] 抓取行情数据...")
        fetch_all_quotes()
    
    # 2. AI分析
    print("\n[2/4] 执行AI分析...")
    analyze_all()
    
    # 3. HTML生成
    print("\n[3/4] 生成HTML报告...")
    generate_html()
    
    # 4. 推送报告
    print("\n[4/4] 推送报告...")
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
    
    run_pipeline(mock=mock_mode, local=local_mode)
