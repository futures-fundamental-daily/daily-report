#!/usr/bin/env python3
"""
期货基本面日报 - HTML生成模块
生成深色主题单页HTML报告
"""

import json
import os
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
ANALYSIS_DIR = BASE_DIR / "analysis"
TEMPLATES_DIR = BASE_DIR / "templates"
OUTPUT_DIR = BASE_DIR / "output"
CONFIG_PATH = BASE_DIR / "config.json"


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_analysis(date_str=None):
    if date_str is None:
        date_str = datetime.now().strftime("%Y%m%d")
    analysis_file = ANALYSIS_DIR / f"analysis_{date_str}.json"
    if not analysis_file.exists():
        raise FileNotFoundError(f"分析数据不存在: {analysis_file}")
    with open(analysis_file, "r", encoding="utf-8") as f:
        return json.load(f)


def get_direction_class(direction):
    if direction == "看多":
        return "bull"
    elif direction == "看空":
        return "bear"
    else:
        return "neutral"


def generate_html():
    """生成HTML报告"""
    config = load_config()
    visual = config["visual"]
    
    try:
        analysis_data = load_analysis()
    except FileNotFoundError:
        print("[ERROR] 分析数据不存在，请先运行 analyzer.py")
        return None
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    time_str = datetime.now().strftime("%H:%M")
    
    # 生成品种卡片HTML
    cards_html = ""
    for item in analysis_data:
        code = item["code"]
        name = item["name"]
        score = item["score"]
        stars = "★" * item["stars"] + "☆" * (3 - item["stars"])
        direction = item["direction"]
        sector = item["sector"]
        timeframe = item["timeframe"]
        confidence = item["confidence"]
        entry = item["entry"]
        stop = item["stop_loss"]
        momentum = item["momentum"]
        summary = item["summary"]
        logic = item["logic"]
        risks = item["risk"]
        quant = item["quant_data"]
        sector_perf = item["sector_performance"]
        quote = item.get("quote", {})
        
        change_pct = quote.get("change_pct", 0)
        close = quote.get("close", 0)
        change_class = "up" if change_pct >= 0 else "down"
        change_sign = "+" if change_pct >= 0 else ""
        
        direction_class = get_direction_class(direction)
        
        # 分析逻辑HTML
        logic_html = ""
        for l in logic:
            logic_html += f'<div class="logic-item">{l}</div>'
        
        # 风险HTML
        risk_html = ""
        for r in risks:
            risk_html += f'<div class="risk-item">⚠️ {r}</div>'
        
        # 关联股票HTML
        related_stocks_html = ""
        if item.get("related_stocks"):
            rs = item["related_stocks"]
            stocks_list = rs.get("stocks", [])
            sector_avg = rs.get("sector_avg_change", 0)
            sector_dir = rs.get("sector_direction", "震荡")
            
            stocks_detail = ""
            for s in stocks_list:
                s_change_class = "up" if s["change_pct"] >= 0 else "down"
                s_sign = "+" if s["change_pct"] >= 0 else ""
                stocks_detail += f'<div class="stock-item"><span class="stock-name">{s["name"]}</span><span class="stock-change {s_change_class}">{s_sign}{s["change_pct"]:.2f}%</span></div>'
            
            avg_class = "up" if sector_avg >= 0 else "down"
            avg_sign = "+" if sector_avg >= 0 else ""
            
            related_stocks_html = f'''
                <div class="section">
                    <div class="section-title">📊 关联股票（板块联动）</div>
                    <div class="sector-avg">板块加权平均: <span class="{avg_class}">{avg_sign}{sector_avg:.2f}%</span> | 情绪: {sector_dir}</div>
                    <div class="stocks-list">
                        {stocks_detail}
                    </div>
                </div>
            '''
        
        card_html = f'''
        <div class="card">
            <div class="card-header" onclick="toggleCard(this)">
                <div class="card-title">
                    <span class="stars">{stars}</span>
                    <span class="product-name">{name} {code}</span>
                    <span class="score">{score}/10</span>
                </div>
                <div class="card-tags">
                    <span class="tag direction-{direction_class}">{direction}</span>
                    <span class="tag sector">{sector}</span>
                    <span class="tag">{timeframe}</span>
                    <span class="tag">置信度:{confidence}</span>
                </div>
                <div class="card-quote">
                    <span class="price">{close:.2f}</span>
                    <span class="change {change_class}">{change_sign}{change_pct:.2f}%</span>
                </div>
            </div>
            <div class="card-body">
                <div class="quick-info">
                    <div class="info-row">
                        <span class="info-label">入场区间</span>
                        <span class="info-value">{entry}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">止损位</span>
                        <span class="info-value stop">{stop}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">动量</span>
                        <span class="info-value">{momentum}</span>
                    </div>
                </div>
                <div class="summary">
                    💡 {summary}
                </div>
                <div class="section">
                    <div class="section-title">AI分析逻辑</div>
                    {logic_html}
                </div>
                <div class="section risk-section">
                    <div class="section-title">⚠️ 风险提示</div>
                    {risk_html}
                </div>
                <div class="section">
                    <div class="section-title">📈 量化数据</div>
                    <div class="quant-grid">
                        <div class="quant-item">
                            <div class="quant-label">近5日涨跌</div>
                            <div class="quant-value {"up" if quant["change_5d"] >= 0 else "down"}">{quant["change_5d"]:.2f}%</div>
                        </div>
                        <div class="quant-item">
                            <div class="quant-label">近20日涨跌</div>
                            <div class="quant-value {"up" if quant["change_20d"] >= 0 else "down"}">{quant["change_20d"]:.2f}%</div>
                        </div>
                        <div class="quant-item">
                            <div class="quant-label">波动率</div>
                            <div class="quant-value">{quant["volatility"]:.2f}%</div>
                        </div>
                    </div>
                </div>
                <div class="section">
                    <div class="section-title">🌍 板块与产区</div>
                    <div class="sector-info">{sector_perf}</div>
                </div>
                {related_stocks_html}
            </div>
        </div>
        '''
        cards_html += card_html
    
    # 完整HTML
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>期货基本面日报 | {date_str}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background-color: {visual["bg_color"]};
            color: #c9d1d9;
            line-height: 1.6;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        header {{
            text-align: center;
            padding: 30px 0;
            border-bottom: 1px solid #30363d;
            margin-bottom: 30px;
        }}
        
        h1 {{
            font-size: 28px;
            color: #f0f6fc;
            margin-bottom: 8px;
        }}
        
        .subtitle {{
            color: #8b949e;
            font-size: 14px;
        }}
        
        .controls {{
            display: flex;
            justify-content: center;
            gap: 12px;
            margin-bottom: 24px;
        }}
        
        .btn {{
            padding: 8px 20px;
            border: 1px solid #30363d;
            background: #21262d;
            color: #c9d1d9;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.2s;
        }}
        
        .btn:hover {{
            background: #30363d;
            border-color: #8b949e;
        }}
        
        .filter-bar {{
            display: flex;
            justify-content: center;
            gap: 8px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }}
        
        .filter-btn {{
            padding: 6px 14px;
            border: 1px solid #30363d;
            background: transparent;
            color: #8b949e;
            border-radius: 20px;
            cursor: pointer;
            font-size: 13px;
            transition: all 0.2s;
        }}
        
        .filter-btn:hover,
        .filter-btn.active {{
            background: {visual["sector_color"]};
            color: #fff;
            border-color: {visual["sector_color"]};
        }}
        
        .card {{
            background: {visual["card_bg"]};
            border: 1px solid #30363d;
            border-radius: 12px;
            margin-bottom: 16px;
            overflow: hidden;
            transition: border-color 0.2s;
        }}
        
        .card:hover {{
            border-color: #484f58;
        }}
        
        .card-header {{
            padding: 16px 20px;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 8px;
        }}
        
        .card-title {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .stars {{
            color: {visual["score_color"]};
            font-size: 16px;
        }}
        
        .product-name {{
            font-size: 16px;
            font-weight: 600;
            color: #f0f6fc;
        }}
        
        .score {{
            font-size: 18px;
            font-weight: 700;
            color: {visual["score_color"]};
        }}
        
        .card-tags {{
            display: flex;
            gap: 6px;
            flex-wrap: wrap;
        }}
        
        .tag {{
            padding: 3px 10px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 500;
        }}
        
        .tag.direction-bull {{
            background: rgba(255, 68, 68, 0.2);
            color: {visual["bull_color"]};
        }}
        
        .tag.direction-bear {{
            background: rgba(63, 185, 80, 0.2);
            color: {visual["down_color"]};
        }}
        
        .tag.direction-neutral {{
            background: rgba(139, 148, 158, 0.2);
            color: #8b949e;
        }}
        
        .tag.sector {{
            background: rgba(31, 111, 235, 0.2);
            color: {visual["sector_color"]};
        }}
        
        .card-quote {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .price {{
            font-size: 18px;
            font-weight: 600;
            color: #f0f6fc;
        }}
        
        .change {{
            font-size: 14px;
            font-weight: 600;
            padding: 2px 8px;
            border-radius: 4px;
        }}
        
        .change.up {{
            background: rgba(255, 68, 68, 0.15);
            color: {visual["up_color"]};
        }}
        
        .change.down {{
            background: rgba(63, 185, 80, 0.15);
            color: {visual["down_color"]};
        }}
        
        .card-body {{
            padding: 0 20px;
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease, padding 0.3s ease;
        }}
        
        .card.expanded .card-body {{
            padding: 0 20px 20px;
            max-height: 2000px;
        }}
        
        .card-header::after {{
            content: "▼";
            font-size: 12px;
            color: #8b949e;
            transition: transform 0.2s;
        }}
        
        .card.expanded .card-header::after {{
            transform: rotate(180deg);
        }}
        
        .quick-info {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            padding: 16px 0;
            border-bottom: 1px solid #30363d;
            margin-bottom: 16px;
        }}
        
        .info-row {{
            text-align: center;
        }}
        
        .info-label {{
            display: block;
            font-size: 12px;
            color: #8b949e;
            margin-bottom: 4px;
        }}
        
        .info-value {{
            font-size: 15px;
            font-weight: 600;
            color: #f0f6fc;
        }}
        
        .info-value.stop {{
            color: {visual["risk_color"]};
        }}
        
        .summary {{
            background: rgba(31, 111, 235, 0.1);
            border-left: 3px solid {visual["sector_color"]};
            padding: 12px 16px;
            border-radius: 0 8px 8px 0;
            margin-bottom: 16px;
            font-size: 14px;
            color: #c9d1d9;
        }}
        
        .section {{
            margin-bottom: 16px;
        }}
        
        .section-title {{
            font-size: 13px;
            font-weight: 600;
            color: #8b949e;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .logic-item {{
            padding: 8px 0;
            border-bottom: 1px solid #21262d;
            font-size: 14px;
            color: #c9d1d9;
        }}
        
        .logic-item:last-child {{
            border-bottom: none;
        }}
        
        .risk-section .section-title {{
            color: {visual["risk_color"]};
        }}
        
        .risk-item {{
            padding: 8px 12px;
            background: rgba(210, 153, 34, 0.1);
            border-radius: 6px;
            margin-bottom: 6px;
            font-size: 13px;
            color: {visual["risk_color"]};
        }}
        
        .quant-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
        }}
        
        .quant-item {{
            text-align: center;
            padding: 12px;
            background: #0d1117;
            border-radius: 8px;
        }}
        
        .quant-label {{
            font-size: 12px;
            color: #8b949e;
            margin-bottom: 4px;
        }}
        
        .quant-value {{
            font-size: 16px;
            font-weight: 700;
            color: #f0f6fc;
        }}
        
        .quant-value.up {{
            color: {visual["up_color"]};
        }}
        
        .quant-value.down {{
            color: {visual["down_color"]};
        }}
        
        .sector-info {{
            font-size: 14px;
            color: #c9d1d9;
            padding: 8px 0;
        }}
        
        .sector-avg {{
            font-size: 14px;
            color: #c9d1d9;
            margin-bottom: 10px;
            padding: 8px 12px;
            background: rgba(31, 111, 235, 0.05);
            border-radius: 6px;
        }}
        
        .stocks-list {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 8px;
        }}
        
        .stock-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 12px;
            background: #0d1117;
            border-radius: 6px;
            font-size: 13px;
        }}
        
        .stock-name {{
            color: #c9d1d9;
        }}
        
        .stock-change {{
            font-weight: 600;
            font-size: 13px;
        }}
        
        .stock-change.up {{
            color: {visual["up_color"]};
        }}
        
        .stock-change.down {{
            color: {visual["down_color"]};
        }}
        
        footer {{
            text-align: center;
            padding: 30px 0;
            color: #484f58;
            font-size: 12px;
            border-top: 1px solid #30363d;
            margin-top: 30px;
        }}
        
        @media (max-width: 600px) {{
            .card-header {{
                flex-direction: column;
                align-items: flex-start;
            }}
            
            .quick-info {{
                grid-template-columns: 1fr;
            }}
            
            .quant-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>期货基本面日报</h1>
            <div class="subtitle">{date_str} {time_str} | 基于多维度量化分析</div>
        </header>
        
        <div class="controls">
            <button class="btn" onclick="expandAll()">展开全部</button>
            <button class="btn" onclick="collapseAll()">收起全部</button>
        </div>
        
        <div class="filter-bar">
            <button class="filter-btn active" onclick="filterSector('all')">全部</button>
            <button class="filter-btn" onclick="filterSector('新能源')">新能源</button>
            <button class="filter-btn" onclick="filterSector('农产品')">农产品</button>
            <button class="filter-btn" onclick="filterSector('有色金属')">有色金属</button>
            <button class="filter-btn" onclick="filterSector('黑色系')">黑色系</button>
            <button class="filter-btn" onclick="filterSector('能源化工')">能源化工</button>
        </div>
        
        <div class="cards-container">
            {cards_html}
        </div>
        
        <footer>
            <p>⚠️ 本报告基于公开信息整理，仅供参考，不构成投资建议。</p>
            <p>数据更新时间：{date_str} {time_str}</p>
        </footer>
    </div>
    
    <script>
        function toggleCard(header) {{
            const card = header.parentElement;
            card.classList.toggle('expanded');
        }}
        
        function expandAll() {{
            document.querySelectorAll('.card').forEach(card => {{
                card.classList.add('expanded');
            }});
        }}
        
        function collapseAll() {{
            document.querySelectorAll('.card').forEach(card => {{
                card.classList.remove('expanded');
            }});
        }}
        
        function filterSector(sector) {{
            // 更新按钮状态
            document.querySelectorAll('.filter-btn').forEach(btn => {{
                btn.classList.remove('active');
                if (btn.textContent === (sector === 'all' ? '全部' : sector)) {{
                    btn.classList.add('active');
                }}
            }});
            
            // 过滤卡片
            document.querySelectorAll('.card').forEach(card => {{
                if (sector === 'all') {{
                    card.style.display = 'block';
                }} else {{
                    const cardSector = card.querySelector('.tag.sector');
                    if (cardSector && cardSector.textContent === sector) {{
                        card.style.display = 'block';
                    }} else {{
                        card.style.display = 'none';
                    }}
                }}
            }});
        }}
    </script>
</body>
</html>
'''
    
    # 保存HTML
    output_file = OUTPUT_DIR / "index.html"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)
    
    # 同时保存到archive
    archive_file = BASE_DIR / "archive" / f"{date_str}.html"
    with open(archive_file, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"[{datetime.now()}] HTML报告已生成")
    print(f"  主文件: {output_file}")
    print(f"  归档: {archive_file}")
    
    return output_file


if __name__ == "__main__":
    generate_html()
