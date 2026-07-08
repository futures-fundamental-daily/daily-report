#!/usr/bin/env python3
"""
期货基本面日报 - Git推送模块
推送HTML到GitHub Pages
"""

import os
import subprocess
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "output"
CONFIG_PATH = BASE_DIR / "config.json"


def load_config():
    import json
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def push_to_github():
    """推送报告到GitHub"""
    config = load_config()
    github = config["github"]
    repo = github["repo"]
    branch = github["branch"]
    commit_prefix = github["commit_prefix"]
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    commit_msg = f"{commit_prefix} {date_str}"
    
    print(f"[{datetime.now()}] 开始推送到GitHub...")
    
    # 检测是否在GitHub Actions中
    in_actions = os.environ.get("GITHUB_ACTIONS", "") == "true"
    
    # 检查git是否初始化
    git_dir = BASE_DIR / ".git"
    if not git_dir.exists():
        print("[INFO] Git仓库未初始化，正在初始化...")
        subprocess.run(["git", "init"], cwd=BASE_DIR, check=True)
    
    # 检查远程仓库（本地环境需要手动配置）
    if not in_actions:
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=BASE_DIR, capture_output=True, text=True
            )
            if result.returncode != 0:
                print("[INFO] 添加远程仓库...")
                # 使用GITHUB_TOKEN环境变量
                token = os.environ.get("GITHUB_TOKEN", "")
                if token:
                    remote_url = f"https://{token}@github.com/{repo}.git"
                else:
                    remote_url = f"https://github.com/{repo}.git"
                subprocess.run(
                    ["git", "remote", "add", "origin", remote_url],
                    cwd=BASE_DIR, check=True
                )
        except Exception as e:
            print(f"[WARN] 检查远程仓库失败: {e}")
    
    # 复制output/index.html到根目录（GitHub Pages需要）
    src = OUTPUT_DIR / "index.html"
    dst = BASE_DIR / "index.html"
    if src.exists():
        import shutil
        shutil.copy2(src, dst)
    
    # 添加文件
    subprocess.run(["git", "add", "index.html", "archive/", "config.json"], cwd=BASE_DIR)
    
    # 提交
    try:
        subprocess.run(
            ["git", "commit", "-m", commit_msg],
            cwd=BASE_DIR, check=True
        )
    except subprocess.CalledProcessError:
        print("[INFO] 没有变更需要提交")
        return
    
    # 推送
    try:
        if in_actions:
            # Actions中actions/checkout已配置好凭证
            subprocess.run(
                ["git", "push", "origin", f"HEAD:{branch}"],
                cwd=BASE_DIR, check=True
            )
        else:
            subprocess.run(
                ["git", "push", "origin", f"HEAD:{branch}"],
                cwd=BASE_DIR, check=True
            )
        print(f"[{datetime.now()}] 推送成功: {commit_msg}")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] 推送失败: {e}")


def push_local():
    """本地模式：仅生成文件不推送"""
    print(f"[{datetime.now()}] 本地模式：跳过Git推送")
    print(f"  HTML文件位于: {OUTPUT_DIR / 'index.html'}")


if __name__ == "__main__":
    import sys
    if "--local" in sys.argv:
        push_local()
    else:
        push_to_github()
