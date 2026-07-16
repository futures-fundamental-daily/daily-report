#!/usr/bin/env python3
"""重新生成指定日期的期货日报HTML"""
import json
import shutil
from datetime import datetime
from pathlib import Path
import sys

BASE_DIR = Path(__file__).parent.parent
ANALYSIS_DIR = BASE_DIR / "analysis"
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"

sys.path.insert(0, str(BASE_DIR / "scripts"))
from generator import generate_html, load_analysis, get_direction_class

# 从现有分析文件读取日期
for date_str in ["20260714", "20260715"]:
    print(f"\n=== 重新生成 {date_str} 的报告 ===")
    
    try:
        analysis_data = load_analysis(date_str)
    except FileNotFoundError:
        print(f"[ERROR] 分析数据不存在: {date_str}")
        continue
    
    # 读取对应的quotes和macro数据
    quotes_file = DATA_DIR / f"quotes_{date_str}.json"
    macro_file = DATA_DIR / f"macro_{date_str}.json"
    
    # 手动生成HTML（hack方式：临时替换datetime.now）
    import generator
    original_now = datetime.now
    
    # 构造假时间
    fake_date = datetime.strptime(date_str, "%Y%m%d")
    fake_time = datetime(fake_date.year, fake_date.month, fake_date.day, 16, 30)
    
    def fake_datetime_now():
        return fake_time
    
    datetime.now = fake_datetime_now
    
    try:
        # 重新加载模块以应用hack
        import importlib
        importlib.reload(generator)
        
        # 生成HTML
        output_file = generator.generate_html()
        
        # 归档
        date_fmt = fake_date.strftime("%Y-%m-%d")
        archive_file = BASE_DIR / "archive" / f"{date_fmt}.html"
        shutil.copy2(output_file, archive_file)
        
        print(f"  ✓ 已生成: {output_file}")
        print(f"  ✓ 已归档: {archive_file}")
    except Exception as e:
        print(f"[ERROR] 生成失败: {e}")
    finally:
        datetime.now = original_now

print("\n=== 更新 report_index.json ===")
from build_index import build_index
build_index()
print("  ✓ 索引已更新")
