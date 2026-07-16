#!/usr/bin/env python3
"""重新生成指定日期的HTML报告"""
import json
import shutil
from datetime import datetime
from pathlib import Path
import sys
import subprocess

BASE_DIR = Path(__file__).parent.parent
ANALYSIS_DIR = BASE_DIR / "analysis"
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"

sys.path.insert(0, str(BASE_DIR / "scripts"))

# 使用 unittest.mock 来 patch datetime.now
from unittest.mock import patch

import generator
import build_index

for date_str in ["20260714", "20260715"]:
    d = datetime.strptime(date_str, "%Y%m%d")
    fake_now = datetime(d.year, d.month, d.day, 16, 30)
    
    print(f"\n=== 重新生成 {d.strftime('%Y-%m-%d')} 的报告 ===")
    
    # patch datetime.now
    with patch('datetime.datetime') as mock_datetime:
        mock_datetime.now.return_value = fake_now
        mock_datetime.strftime = datetime.strftime
        mock_datetime.strptime = datetime.strptime
        mock_datetime.__name__ = 'datetime'
        
        # 重新加载generator以应用patch
        import importlib
        importlib.reload(generator)
        
        try:
            output_file = generator.generate_html()
            
            # 归档
            archive_file = BASE_DIR / "archive" / f"{d.strftime('%Y-%m-%d')}.html"
            shutil.copy2(output_file, archive_file)
            
            print(f"  ✓ 已生成: {output_file}")
            print(f"  ✓ 已归档: {archive_file}")
        except Exception as e:
            print(f"[ERROR] 生成失败: {e}")

print("\n=== 更新 report_index.json ===")
importlib.reload(build_index)
build_index.build_index()
print("  ✓ 索引已更新")

print("\n=== 推送到 GitHub ===")
subprocess.run(["git", "add", "-A"], cwd=BASE_DIR, check=True)
subprocess.run(["git", "commit", "-m", f"daily: regenerate 2026-07-14 & 2026-07-15"], cwd=BASE_DIR, check=True)
subprocess.run(["git", "push", "origin", "main"], cwd=BASE_DIR, check=True)
print("  ✓ 已推送")
