#!/usr/bin/env python3
"""
期货基本面日报 - 数据守护者模块 v1.0
严格陈旧数据检测 + 自动报警

检测维度：
1. 单日陈旧：close/volume/open_interest/change_pct 全部与昨日相同
2. 连续陈旧：连续 N 天数据完全相同
3. 异常冻结：change_pct=0 但 volume>0（数据源可能冻结）
4. 数据降级：akshare 失败回退到 mock 数据
5. 大面积异常：超过阈值比例品种数据异常

报警机制：
- 飞书消息推送（复用现有凭证）
- 报警去重（24h内同一问题不重复报警）
- 报警级别：WARNING / CRITICAL
"""

import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
GUARDIAN_STATE_PATH = LOGS_DIR / "guardian_state.json"
ALERT_LOG_PATH = LOGS_DIR / "alerts.json"

# 飞书凭证路径（复用 stock-assistant 配置）
STOCK_CONFIG_PATH = Path("/root/.openclaw/skills/stock-assistant/config.json")
FEISHU_USER_ID = "ou_07cd0cc6493aeeca940cf3091e4fdb75"


def _load_guardian_state() -> dict:
    """加载守护者状态（报警记录、数据源健康度）"""
    if GUARDIAN_STATE_PATH.exists():
        try:
            with open(GUARDIAN_STATE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "last_alert_hashes": {},  # hash -> timestamp
        "data_source_health": {},  # source -> {last_ok, fail_count, status}
        "consecutive_stale": {},   # code -> days
        "version": "1.0"
    }


def _save_guardian_state(state: dict):
    """保存守护者状态"""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    with open(GUARDIAN_STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def _load_prev_quotes(days_back: int = 1) -> Optional[Dict]:
    """加载 N 天前的数据"""
    target_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y%m%d")
    prev_file = DATA_DIR / f"quotes_{target_date}.json"
    if prev_file.exists():
        try:
            with open(prev_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return None


def _compute_data_fingerprint(data: dict) -> str:
    """计算数据指纹（用于检测连续多天不变）"""
    keys = ["close", "change_pct", "volume", "open_interest"]
    values = [str(data.get(k, "N/A")) for k in keys]
    return hashlib.md5("|".join(values).encode()).hexdigest()[:16]


def _should_alert(alert_key: str, cooldown_hours: int = 24) -> bool:
    """检查是否应该在冷却期后再次报警"""
    state = _load_guardian_state()
    last_alert = state.get("last_alert_hashes", {}).get(alert_key)
    if not last_alert:
        return True
    last_time = datetime.fromisoformat(last_alert)
    if datetime.now() - last_time > timedelta(hours=cooldown_hours):
        return True
    return False


def _record_alert(alert_key: str):
    """记录报警时间"""
    state = _load_guardian_state()
    state.setdefault("last_alert_hashes", {})[alert_key] = datetime.now().isoformat()
    _save_guardian_state(state)


def _get_feishu_token() -> Optional[str]:
    """获取飞书 tenant_access_token"""
    try:
        import requests
        if not STOCK_CONFIG_PATH.exists():
            return None
        with open(STOCK_CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        feishu_cfg = cfg.get("feishu", {})
        app_id = feishu_cfg.get("app_id")
        app_secret = feishu_cfg.get("app_secret")
        if not app_id or not app_secret:
            return None
        resp = requests.post(
            "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
            json={"app_id": app_id, "app_secret": app_secret},
            timeout=10
        )
        data = resp.json()
        if data.get("code") == 0:
            return data["tenant_access_token"]
    except Exception as e:
        print(f"[Guardian] 获取飞书token失败: {e}")
    return None


def _send_feishu_alert(title: str, body: str, level: str = "WARNING"):
    """发送飞书报警消息"""
    try:
        import requests
        token = _get_feishu_token()
        if not token:
            print("[Guardian] 飞书凭证未配置，跳过报警推送")
            return False

        emoji = "🚨" if level == "CRITICAL" else "⚠️"
        message = f"{emoji} **{title}**\n\n{body}\n\n---\n🤖 数据守护者 | {datetime.now().strftime('%H:%M:%S')}"

        resp = requests.post(
            "https://open.feishu.cn/open-apis/im/v1/messages",
            headers={"Authorization": f"Bearer {token}"},
            params={"receive_id_type": "open_id"},
            json={
                "receive_id": FEISHU_USER_ID,
                "msg_type": "text",
                "content": json.dumps({"text": message}, ensure_ascii=False)
            },
            timeout=10
        )
        result = resp.json()
        if result.get("code") == 0:
            print(f"[Guardian] 飞书报警已发送 [{level}]")
            return True
        else:
            print(f"[Guardian] 飞书报警发送失败: {result}")
    except Exception as e:
        print(f"[Guardian] 飞书报警异常: {e}")
    return False


# =============================================================================
# 核心检测函数
# =============================================================================

def detect_single_day_stale(current: dict, previous: dict) -> bool:
    """
    检测单日陈旧数据
    比较字段：close, change_pct, volume, open_interest
    全部相同才判定为陈旧
    """
    if not previous:
        return False
    keys = ["close", "change_pct", "volume", "open_interest"]
    for k in keys:
        if current.get(k) != previous.get(k):
            return False
    return True


def detect_consecutive_stale(code: str, current: dict, days: int = 3) -> Tuple[bool, int]:
    """
    检测连续 N 天数据不变
    返回: (是否连续陈旧, 连续天数)
    """
    current_fp = _compute_data_fingerprint(current)
    consecutive = 0

    for d in range(1, days + 1):
        prev = _load_prev_quotes(d)
        if not prev or code not in prev:
            break
        prev_fp = _compute_data_fingerprint(prev[code])
        if prev_fp == current_fp:
            consecutive += 1
        else:
            break

    return consecutive >= 2, consecutive


def detect_frozen_data(data: dict) -> bool:
    """
    检测数据源冻结异常
    change_pct=0 但 volume>0：可能是数据源停止更新但返回旧值
    """
    change = data.get("change_pct", None)
    volume = data.get("volume", 0)
    if change == 0 and volume > 0:
        # 进一步检查：如果价格也很"整"（如 38000.0, 2800.0），更像 mock
        close = data.get("close", 0)
        if close > 0 and close == int(close):
            return True
    return False


def detect_mock_fallback(data: dict) -> bool:
    """检测是否使用了 mock 数据兜底"""
    return data.get("data_source") == "mock"


# =============================================================================
# 主检测入口
# =============================================================================

def inspect_all_quotes(quotes: Dict[str, dict], products: List[dict]) -> Dict:
    """
    全面检查所有品种数据质量
    
    返回检测报告：
    {
        "summary": {...},
        "stale_single": [...],
        "stale_consecutive": [...],
        "frozen": [...],
        "mock_fallback": [...],
        "alerts_sent": [...]
    }
    """
    state = _load_guardian_state()
    stale_single = []
    stale_consecutive = []
    frozen = []
    mock_fallback = []
    alerts_sent = []

    prev_quotes = _load_prev_quotes(1)
    date_str = datetime.now().strftime("%Y-%m-%d")

    print(f"\n[Guardian] 开始数据质量检查...")

    for p in products:
        code = p["code"]
        name = p["name"]
        if code not in quotes:
            continue

        data = quotes[code]

        # 1. 单日陈旧检测
        if prev_quotes and code in prev_quotes:
            if detect_single_day_stale(data, prev_quotes[code]):
                stale_single.append({
                    "code": code, "name": name,
                    "close": data["close"], "change_pct": data["change_pct"],
                    "reason": "与昨日数据完全相同"
                })

        # 2. 连续陈旧检测
        is_consecutive, days = detect_consecutive_stale(code, data, days=3)
        if is_consecutive:
            stale_consecutive.append({
                "code": code, "name": name,
                "days": days,
                "close": data["close"]
            })

        # 3. 冻结检测
        if detect_frozen_data(data):
            frozen.append({
                "code": code, "name": name,
                "close": data["close"], "volume": data["volume"]
            })

        # 4. mock 降级检测
        if detect_mock_fallback(data):
            mock_fallback.append({
                "code": code, "name": name,
                "close": data["close"]
            })

    # 汇总
    total = len(products)
    summary = {
        "date": date_str,
        "total": total,
        "stale_single": len(stale_single),
        "stale_consecutive": len(stale_consecutive),
        "frozen": len(frozen),
        "mock_fallback": len(mock_fallback),
        "healthy": total - len(stale_single) - len(mock_fallback)
    }

    print(f"[Guardian] 检查结果: {summary['healthy']}/{total} 健康")
    if stale_single:
        print(f"  ⚠ 单日陈旧: {len(stale_single)} 个")
    if stale_consecutive:
        print(f"  🚨 连续陈旧: {len(stale_consecutive)} 个")
    if frozen:
        print(f"  ❄ 数据冻结: {len(frozen)} 个")
    if mock_fallback:
        print(f"  🎲 Mock兜底: {len(mock_fallback)} 个")

    # ===== 报警逻辑 =====

    # 1. 大面积异常（>50%品种陈旧或mock）→ CRITICAL
    bad_ratio = (len(stale_single) + len(mock_fallback)) / total if total else 0
    if bad_ratio >= 0.5:
        alert_key = f"mass_failure_{date_str}"
        if _should_alert(alert_key, cooldown_hours=6):
            title = "期货日报数据源大面积异常"
            body = (
                f"📊 **{date_str} 数据质量报告**\n\n"
                f"🚨 **CRITICAL**：{len(stale_single)}个品种数据陈旧，"
                f"{len(mock_fallback)}个品种使用模拟数据\n"
                f"异常比例：**{bad_ratio*100:.0f}%**\n\n"
                f"陈旧品种: {', '.join(s['code'] for s in stale_single)}\n"
                f"Mock兜底: {', '.join(m['code'] for m in mock_fallback)}\n\n"
                f"⚡ 建议：立即检查 akshare / 新浪数据源"
            )
            if _send_feishu_alert(title, body, level="CRITICAL"):
                _record_alert(alert_key)
                alerts_sent.append(alert_key)

    # 2. 连续陈旧 → CRITICAL
    for item in stale_consecutive:
        alert_key = f"stale_consecutive_{item['code']}_{date_str}"
        if _should_alert(alert_key, cooldown_hours=12):
            title = f"{item['name']}({item['code']}) 连续{item['days']}天数据未更新"
            body = (
                f"🔁 **连续陈旧警告**\n\n"
                f"品种: {item['name']}({item['code']})\n"
                f"连续天数: **{item['days']} 天**\n"
                f"当前价格: {item['close']}\n\n"
                f"该品种数据已连续多天完全相同，数据源可能已停止更新。"
            )
            if _send_feishu_alert(title, body, level="CRITICAL"):
                _record_alert(alert_key)
                alerts_sent.append(alert_key)

    # 3. 单日陈旧（非连续）→ WARNING（合并为一条消息）
    if stale_single and not stale_consecutive:
        stale_only_single = [s for s in stale_single
                             if not any(sc["code"] == s["code"] for sc in stale_consecutive)]
        if stale_only_single:
            alert_key = f"stale_single_{date_str}"
            if _should_alert(alert_key, cooldown_hours=24):
                items_text = "\n".join(
                    f"• {s['name']}({s['code']}): {s['close']:.2f} ({s['change_pct']:+.2f}%)"
                    for s in stale_only_single[:5]
                )
                more = f"\n... 等共 {len(stale_only_single)} 个品种" if len(stale_only_single) > 5 else ""
                title = f"{date_str} 期货数据陈旧警告"
                body = (
                    f"⚠️ **以下品种数据与昨日完全相同，可能存在数据源问题**\n\n"
                    f"{items_text}{more}\n\n"
                    f"📌 请检查 akshare 数据源是否正常返回当日行情"
                )
                if _send_feishu_alert(title, body, level="WARNING"):
                    _record_alert(alert_key)
                    alerts_sent.append(alert_key)

    # 4. Mock 降级 → WARNING（合并为一条）
    if mock_fallback:
        alert_key = f"mock_fallback_{date_str}"
        if _should_alert(alert_key, cooldown_hours=24):
            items_text = "\n".join(
                f"• {m['name']}({m['code']}): {m['close']:.2f}"
                for m in mock_fallback
            )
            title = f"{date_str} 部分品种使用模拟数据"
            body = (
                f"🎲 **数据源降级警告**\n\n"
                f"以下品种因 akshare 获取失败，已使用模拟数据兜底：\n\n"
                f"{items_text}\n\n"
                f"⚠️ 模拟数据仅供参考，不代表真实行情"
            )
            if _send_feishu_alert(title, body, level="WARNING"):
                _record_alert(alert_key)
                alerts_sent.append(alert_key)

    # 保存检测报告
    report = {
        "summary": summary,
        "stale_single": stale_single,
        "stale_consecutive": stale_consecutive,
        "frozen": frozen,
        "mock_fallback": mock_fallback,
        "alerts_sent": alerts_sent,
        "checked_at": datetime.now().isoformat()
    }

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = LOGS_DIR / f"guardian_report_{date_str}.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    return report


# =============================================================================
# 便捷入口
# =============================================================================

def run_guardian_check(quotes: Dict[str, dict], products: List[dict]) -> Dict:
    """主入口：运行完整的数据质量检查"""
    return inspect_all_quotes(quotes, products)


if __name__ == "__main__":
    # 测试：加载今天的数据并检查
    import sys
    sys.path.insert(0, str(BASE_DIR / "scripts"))
    from fetcher import load_config

    config = load_config()
    products = config["products"]

    date_str = datetime.now().strftime("%Y%m%d")
    quote_file = DATA_DIR / f"quotes_{date_str}.json"
    if quote_file.exists():
        with open(quote_file, "r", encoding="utf-8") as f:
            quotes = json.load(f)
        report = run_guardian_check(quotes, products)
        print("\n检测报告:")
        print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    else:
        print(f"[Guardian] 今日数据文件不存在: {quote_file}")
