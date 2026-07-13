#!/usr/bin/env python3
"""
期货基本面日报 - 宏观数据模块
接入akshare获取宏观数据
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"


def fetch_macro_data():
    """
    获取宏观数据
    返回: dict 包含各类宏观指标
    """
    print(f"[{datetime.now()}] 开始获取宏观数据...")
    
    results = {
        "update_time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "indicators": []
    }
    
    # 1. CPI/PPI 数据
    try:
        import akshare as ak
        cpi_df = ak.macro_china_cpi()
        if len(cpi_df) > 0:
            latest = cpi_df.iloc[0]
            results["indicators"].append({
                "name": "CPI同比",
                "value": f"{latest.get('全国-当月', 'N/A')}%",
                "trend": "通胀" if float(str(latest.get('全国-当月', 0)).replace('%','') or 0) > 2 else "通缩",
                "impact": "中性"
            })
    except Exception as e:
        print(f"[WARN] CPI获取失败: {e}")
    
    # 2. PPI 数据
    try:
        import akshare as ak
        ppi_df = ak.macro_china_ppi()
        if len(ppi_df) > 0:
            latest = ppi_df.iloc[0]
            ppi_val = float(str(latest.get('当月', 0)).replace('%','') or 0)
            results["indicators"].append({
                "name": "PPI同比",
                "value": f"{latest.get('当月', 'N/A')}%",
                "trend": "通胀" if ppi_val > 0 else "通缩",
                "impact": "利好商品" if ppi_val > 0 else "利空商品"
            })
    except Exception as e:
        print(f"[WARN] PPI获取失败: {e}")
    
    # 3. PMI 数据
    try:
        import akshare as ak
        pmi_df = ak.macro_china_pmi()
        if len(pmi_df) > 0:
            latest = pmi_df.iloc[0]
            pmi_val = float(latest.get('制造业-指数', 0) or 0)
            results["indicators"].append({
                "name": "制造业PMI",
                "value": f"{pmi_val:.1f}",
                "trend": "扩张" if pmi_val > 50 else "收缩",
                "impact": "利好" if pmi_val > 50 else "利空"
            })
    except Exception as e:
        print(f"[WARN] PMI获取失败: {e}")
    
    # 4. 汇率（美元/人民币）
    try:
        # 使用新浪汇率API
        import requests
        resp = requests.get("https://hq.sinajs.cn/list=fx_susdcny", headers={"Referer": "https://finance.sina.com.cn"}, timeout=10)
        if resp.status_code == 200:
            text = resp.content.decode("gbk", errors="ignore")
            if 'var hq_str_fx_susdcny=' in text:
                data_str = text.split('"')[1]
                parts = data_str.split(",")
                if len(parts) >= 8:
                    rate = float(parts[8])  # 当前汇率
                    results["indicators"].append({
                        "name": "USD/CNY",
                        "value": f"{rate:.4f}",
                        "trend": "贬值" if rate > 7.2 else "稳定",
                        "impact": "利好出口" if rate > 7.0 else "中性"
                    })
    except Exception as e:
        print(f"[WARN] 汇率获取失败: {e}")
    
    # 5. 利率（LPR）
    try:
        import akshare as ak
        lpr_df = ak.macro_china_lpr()
        if len(lpr_df) > 0:
            latest = lpr_df.iloc[0]
            lpr_1y = float(str(latest.get('1年期', 0)).replace('%','') or 0)
            results["indicators"].append({
                "name": "1年期LPR",
                "value": f"{lpr_1y:.2f}%",
                "trend": "宽松" if lpr_1y < 3.5 else "紧缩",
                "impact": "利好" if lpr_1y < 3.5 else "中性"
            })
    except Exception as e:
        print(f"[WARN] LPR获取失败: {e}")
    
    # 6. M2增速
    try:
        import akshare as ak
        m2_df = ak.macro_china_m2_yearly()
        if len(m2_df) > 0:
            latest = m2_df.iloc[0]
            m2_val = float(str(latest.get('M2', latest.get('value', 0))).replace('%','') or 0)
            results["indicators"].append({
                "name": "M2同比",
                "value": f"{m2_val:.1f}%",
                "trend": "宽松" if m2_val > 10 else "中性",
                "impact": "利好" if m2_val > 10 else "中性"
            })
    except Exception as e:
        print(f"[WARN] M2获取失败: {e}")
    
    # 7. 存款准备金率
    try:
        import akshare as ak
        rrr_df = ak.macro_china_reserve_requirement_ratio()
        if len(rrr_df) > 0:
            latest = rrr_df.iloc[0]
            rrr_val = float(str(latest.get('大型金融机构-调整后的存款准备金率', 0)).replace('%','') or 0)
            results["indicators"].append({
                "name": "存款准备金率",
                "value": f"{rrr_val:.1f}%",
                "trend": "宽松" if rrr_val < 15 else "紧缩",
                "impact": "利好" if rrr_val < 15 else "中性"
            })
    except Exception as e:
        print(f"[WARN] 准备金率获取失败: {e}")
    
    # 保存数据
    date_str = datetime.now().strftime("%Y%m%d")
    output_file = DATA_DIR / f"macro_{date_str}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"[{datetime.now()}] 宏观数据获取完成，已保存: {output_file}")
    print(f"  共获取 {len(results['indicators'])} 个指标")
    
    return results


def get_macro_summary():
    """
    获取宏观环境总结文本
    """
    date_str = datetime.now().strftime("%Y%m%d")
    macro_file = DATA_DIR / f"macro_{date_str}.json"
    
    if not macro_file.exists():
        return "宏观数据暂未更新"
    
    with open(macro_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    indicators = data.get("indicators", [])
    if not indicators:
        return "宏观数据暂未更新"
    
    # 生成摘要
    summary_parts = []
    for ind in indicators:
        summary_parts.append(f"{ind['name']}{ind['value']}({ind['trend']})")
    
    return "；".join(summary_parts[:4])  # 取前4个关键指标


if __name__ == "__main__":
    results = fetch_macro_data()
    print(json.dumps(results, ensure_ascii=False, indent=2))
    print("\n宏观摘要:")
    print(get_macro_summary())
