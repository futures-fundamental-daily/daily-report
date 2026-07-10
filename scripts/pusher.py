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
    github = config.get("github", {})
    repo = github.get("repo", "")
    branch = github.get("branch", "main")
    commit_prefix = github.get("commit_prefix", "daily:")
    
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


def push_to_feishu():
    """推送日报摘要到飞书（通过飞书OpenAPI）"""
    import json
    import requests
    
    config = load_config()
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    # 读取分析数据（使用最近一个交易日的数据）
    analysis_dir = BASE_DIR / "analysis"
    analysis_files = sorted(analysis_dir.glob("analysis_*.json"), reverse=True)
    if not analysis_files:
        print(f"[WARN] 未找到分析文件")
        return
    
    analysis_file = analysis_files[0]
    with open(analysis_file, "r", encoding="utf-8") as f:
        analysis = json.load(f)
    
    # 从stock-assistant配置读取飞书凭证
    stock_config_path = Path("/root/.openclaw/skills/stock-assistant/config.json")
    feishu_app_id = None
    feishu_app_secret = None
    feishu_user_id = "ou_07cd0cc6493aeeca940cf3091e4fdb75"
    
    if stock_config_path.exists():
        with open(stock_config_path, "r", encoding="utf-8") as f:
            stock_config = json.load(f)
        feishu_cfg = stock_config.get("feishu", {})
        feishu_app_id = feishu_cfg.get("app_id")
        feishu_app_secret = feishu_cfg.get("app_secret")
        feishu_user_id = feishu_cfg.get("user_id", feishu_user_id)
    
    if not feishu_app_id or not feishu_app_secret:
        print("[WARN] 飞书凭证未配置，跳过飞书推送")
        return
    
    # 获取 tenant_access_token
    try:
        resp = requests.post(
            "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
            json={"app_id": feishu_app_id, "app_secret": feishu_app_secret},
            timeout=10
        )
        token_data = resp.json()
        if token_data.get("code") != 0:
            print(f"[ERROR] 获取飞书token失败: {token_data}")
            return
        access_token = token_data["tenant_access_token"]
    except Exception as e:
        print(f"[ERROR] 获取飞书token异常: {e}")
        return
    
    # 构建摘要消息
    top_gainers = sorted([a for a in analysis if a["quote"]["change_pct"] > 0], 
                         key=lambda x: x["quote"]["change_pct"], reverse=True)[:3]
    top_score = sorted(analysis, key=lambda x: x["score"], reverse=True)[:3]
    
    lines = [f"📊 期货基本面日报 | {date_str} 开盘前", ""]
    
    lines.append("🔥 涨幅领先")
    for item in top_gainers:
        q = item["quote"]
        lines.append(f"{item['name']}({item['code']}) {q['change_pct']:+.2f}%")
    
    lines.append("")
    lines.append("⭐ 综合评分 TOP3")
    for i, item in enumerate(top_score, 1):
        lines.append(f"{i}\uFE0F\u20E3 {item['name']}({item['code']}) {item['score']}分 — {item['summary']}")
    
    # 收集风险提示
    risks = []
    for item in analysis:
        if item.get("risk"):
            for r in item["risk"]:
                if r not in risks:
                    risks.append(r)
    
    if risks:
        lines.append("")
        lines.append("⚠️ 核心风险")
        for r in risks[:5]:
            lines.append(f"• {r}")
    
    lines.append("")
    lines.append("📌 操作提示：观望为主，等待方向确认")
    lines.append(f"\n数据来源：{date_str} 收盘 | 新浪期货API")
    
    message = "\n".join(lines)
    
    print(f"[{datetime.now()}] 推送飞书消息...")
    
    # 调用飞书API发送消息
    try:
        resp = requests.post(
            "https://open.feishu.cn/open-apis/im/v1/messages",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"receive_id_type": "open_id"},
            json={
                "receive_id": feishu_user_id,
                "msg_type": "text",
                "content": json.dumps({"text": message}, ensure_ascii=False)
            },
            timeout=10
        )
        result = resp.json()
        if result.get("code") == 0:
            print(f"[{datetime.now()}] 飞书推送成功 ✅")
        else:
            print(f"[ERROR] 飞书推送失败: {result}")
    except Exception as e:
        print(f"[ERROR] 飞书推送异常: {e}")


def push_all():
    """全渠道推送：GitHub + 飞书"""
    try:
        push_to_github()
    except Exception as e:
        print(f"[WARN] GitHub推送失败（不影响飞书）: {e}")
    try:
        push_to_feishu()
    except Exception as e:
        print(f"[ERROR] 飞书推送失败: {e}")


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
