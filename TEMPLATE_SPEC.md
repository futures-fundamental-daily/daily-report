# 期货日报模板规范 (Template Specification)

> **必读**：每次生成新日报前，检查此文档。确保输出与现有样式 100% 一致。

---

## 1. 颜色变量 (CSS Variables)

```css
:root {
  --bg: #0d1117;
  --card-bg: #161b22;
  --card-hover: #1c2128;
  --border: #30363d;
  --border-light: #484f58;
  --text: #e6edf3;
  --text-muted: #8b949e;
  --accent: #d4a853;
  --accent-hover: #c49a43;
  --up: #ff4444;
  --down: #3fb950;
  --neutral: #8b949e;
}
```

**禁止修改**。所有组件必须使用这些变量。

---

## 2. 页面结构 (HTML)

```html
<div class="container">
  <header>
    <h1>期货基本面日报</h1>
    <div class="subtitle">{date_str} {time_str} | 基于多维度量化分析</div>
  </header>

  <!-- 控制栏 -->
  <div class="controls">
    <button class="btn" onclick="expandAll()">展开全部</button>
    <button class="btn" onclick="collapseAll()">收起全部</button>
  </div>

  <!-- 筛选栏 -->
  <div class="filter-bar">
    <button class="filter-btn active" onclick="filterSector('all')">全部</button>
    <button class="filter-btn" onclick="filterSector('新能源')">新能源</button>
    <button class="filter-btn" onclick="filterSector('农产品')">农产品</button>
    <button class="filter-btn" onclick="filterSector('有色金属')">有色金属</button>
    <button class="filter-btn" onclick="filterSector('黑色系')">黑色系</button>
    <button class="filter-btn" onclick="filterSector('能源化工')">能源化工</button>
  </div>

  <!-- 卡片容器 -->
  <div class="cards-container">
    {cards_html}
  </div>

  <footer>
    <p>⚠️ 本报告基于公开信息整理，仅供参考，不构成投资建议。</p>
    <p>数据更新时间：{date_str} {time_str}</p>
  </footer>
</div>
```

---

## 3. 移动端适配 (@media max-width: 600px)

**必须完整包含以下规则**，不可遗漏：

```css
@media (max-width: 600px) {
  .container { padding: 12px; }

  /* Header：单行 flex，不换行 */
  header {
    display: flex;
    flex-direction: row;
    flex-wrap: nowrap;
    align-items: baseline;
    padding: 8px 0;
    margin-bottom: 8px;
    border-bottom: 1px solid #30363d;
  }
  h1 {
    font-size: 15px;
    margin: 0;
    margin-right: 8px;
    white-space: nowrap;
    flex-shrink: 0;
  }
  .subtitle {
    font-size: 11px;
    color: #8b949e;
    margin: 0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  /* 隐藏控制栏和筛选栏（移动端太占地方） */
  .controls { display: none; }
  .filter-bar { display: none; }
  .cards-container { margin-top: 0; }

  /* 卡片 */
  .card { margin-bottom: 10px; border-radius: 8px; }
  .card-header { padding: 10px 12px; flex-direction: column; align-items: flex-start; gap: 6px; }
  .card-header::after { align-self: flex-end; margin-top: -20px; }
  .card-title { gap: 6px; }
  .stars { font-size: 14px; }
  .product-name { font-size: 14px; }
  .score { font-size: 16px; }
  .card-tags { gap: 4px; }
  .tag { padding: 2px 8px; font-size: 11px; }
  .card-quote { gap: 6px; }
  .price { font-size: 16px; }
  .change { font-size: 13px; padding: 1px 6px; }
  .card-body { padding: 0 12px; }
  .card.expanded .card-body { padding: 0 12px 12px; }

  /* Quick Info 三列 */
  .quick-info { grid-template-columns: repeat(3, 1fr); gap: 8px; padding: 10px 0; margin-bottom: 10px; }
  .info-label { font-size: 11px; }
  .info-value { font-size: 13px; }

  .summary { padding: 8px 12px; font-size: 13px; margin-bottom: 10px; }
  .section { margin-bottom: 10px; }
  .section-title { font-size: 12px; margin-bottom: 6px; }
  .logic-item { padding: 6px 0; font-size: 13px; }
  .risk-item { padding: 6px 10px; font-size: 12px; margin-bottom: 4px; }

  /* Quant Grid 三列 */
  .quant-grid { grid-template-columns: repeat(3, 1fr); gap: 8px; }
  .quant-item { padding: 8px; }
  .quant-label { font-size: 11px; }
  .quant-value { font-size: 14px; }

  .sector-info { font-size: 13px; }
  .sector-avg { font-size: 13px; padding: 6px 10px; }

  /* 关联股票两列 */
  .stocks-list { grid-template-columns: repeat(2, 1fr); gap: 6px; }
  .stock-item { padding: 6px 10px; font-size: 12px; }

  footer { padding: 12px 0; margin-top: 12px; font-size: 11px; }
}
```

**关键要求：**
- Header **必须是 flex row**，h1 和 subtitle 单行显示
- `.controls` 和 `.filter-bar` 在移动端 **必须隐藏**
- 所有字号、padding 必须按上表精确执行

---

## 4. 卡片组件 (Card)

### 结构
```html
<div class="card">
  <div class="card-header" onclick="toggleCard(this)">
    <div class="card-title">
      <span class="stars">{stars}</span>
      <span class="product-name">{name} {code}</span>
      <span class="score">{score}/10</span>
    </div>
    <div class="card-tags">
      <span class="tag {direction_class}">{direction}</span>
      <span class="tag sector">{sector}</span>
      <span class="tag">{timeframe}</span>
      <span class="tag">置信度:{confidence}</span>
    </div>
    <div class="card-quote">
      <span class="price">{close}</span>
      <span class="change {up|down}">{change_pct}%</span>
    </div>
  </div>
  <div class="card-body">
    <!-- Quick Info -->
    <div class="quick-info">
      <div class="info-item"><div class="info-label">开仓价</div><div class="info-value">{entry}</div></div>
      <div class="info-item"><div class="info-label">止损价</div><div class="info-value">{stop}</div></div>
      <div class="info-item"><div class="info-label">动量</div><div class="info-value">{momentum}</div></div>
    </div>
    <!-- Summary -->
    <div class="summary">{summary}</div>
    <!-- Sections... -->
  </div>
</div>
```

### 交互
- `toggleCard(header)`：切换 `.expanded` 类
- `expandAll()` / `collapseAll()`：全部展开/收起
- `filterSector(sector)`：按板块筛选显示

---

## 5. 交互脚本 (JavaScript)

必须包含：

```javascript
function toggleCard(header) {
  const card = header.parentElement;
  card.classList.toggle('expanded');
}

function expandAll() {
  document.querySelectorAll('.card').forEach(c => c.classList.add('expanded'));
}

function collapseAll() {
  document.querySelectorAll('.card').forEach(c => c.classList.remove('expanded'));
}

function filterSector(sector) {
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  event.target.classList.add('active');
  document.querySelectorAll('.card').forEach(card => {
    if (sector === 'all') {
      card.style.display = 'block';
    } else {
      const tags = card.querySelectorAll('.tag.sector');
      const match = Array.from(tags).some(t => t.textContent === sector);
      card.style.display = match ? 'block' : 'none';
    }
  });
}
```

---

## 6. 文件输出规范

1. **主文件**：`output/index.html`（当日报告）
2. **归档文件**：`archive/YYYY-MM-DD.html`（历史归档）
3. **索引文件**：生成后必须调用 `build_index.py` 更新 `report_index.json`

---

## 7. 修改记录

| 日期 | 修改内容 |
|------|----------|
| 2026-07-10 | body 添加 `overflow-y: auto; -webkit-overflow-scrolling: touch;` 修复移动端初始无法滚动 |
| 2026-07-10 | iframe 从 display:none 改为 visibility:hidden 解决移动端 onload 丢失 |
| 2026-07-10 | 添加 report_viewer.html + report_list.html 前端系统 |
