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

## 5. report_viewer.html 查阅中心规范

### 5.1 布局结构
```
.app (flex, height: 100vh)
  ├── .sidebar (固定宽度 280px, 可折叠)
  │   ├── .sidebar-header (Logo + 搜索)
  │   ├── .sidebar-scroll (日历 + 最近报告 + 板块筛选 + 收藏)
  │   └── .sidebar-footer (快捷键提示)
  └── .main (flex: 1, flex-direction: column)
      ├── .toolbar (日期、方向、操作按钮)
      ├── .mobile-date-bar (移动端顶部日期条, display: none 默认)
      └── .content (flex: 1, position: relative)
          ├── .loading (绝对定位遮罩)
          └── iframe (加载日报)
```

### 5.2 移动端适配 (@media max-width: 768px)

**必须执行以下规则：**

```css
@media (max-width: 768px) {
  .sidebar { position: fixed; left: 0; top: 0; bottom: 0; z-index: 100;
    transform: translateX(-100%); width: 280px; }
  .sidebar.open { transform: translateX(0); }
  .sidebar-overlay.open { display: block; }
  .mobile-toggle { display: flex; }  /* 右下角悬浮菜单按钮 */
  .toolbar { display: none; }       /* 隐藏 toolbar */
  .keyboard-hint { display: none; }
  .mobile-date-bar { display: flex; } /* 显示顶部日期条 */
  .bottom-cal-bar { display: none !important; } /* 彻底隐藏底部日历条 */
}
```

### 5.3 移动端顶部日期条 (.mobile-date-bar)

```css
.mobile-date-bar {
  display: none;
  height: 72px; flex-shrink: 0;
  border-bottom: 1px solid var(--border);
  background: var(--card-bg);
  overflow-x: auto;
  overflow-y: hidden;          /* 禁止垂直滚动 */
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
  padding: 10px 8px;
  align-items: center;
  flex-wrap: nowrap;           /* 禁止换行 */
}
.mobile-date-bar::-webkit-scrollbar { display: none; }

/* 总览按钮 */
.mobile-date-bar .date-bar-btn {
  display: flex; align-items: center; justify-content: center;
  min-width: 64px; height: 52px; border-radius: 10px; margin-right: 8px;
  background: var(--bg); border: 1px solid var(--border); color: var(--accent);
  font-size: 12px; font-weight: 600; cursor: pointer; flex-shrink: 0;
}

/* 日期项 */
.mobile-date-item {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  min-width: 48px; height: 52px; border-radius: 10px; margin-right: 6px;
  cursor: pointer; border: 1px solid transparent; flex-shrink: 0; position: relative;
}
.mobile-date-item .d-week { font-size: 10px; color: var(--text-muted); }
.mobile-date-item .d-num { font-size: 15px; font-weight: 700; color: var(--text); }
.mobile-date-item.has-report { border-color: var(--accent); }
.mobile-date-item.has-report .d-num { color: var(--accent); }
.mobile-date-item.active { background: var(--accent); border-color: var(--accent); }
.mobile-date-item.active .d-week, .mobile-date-item.active .d-num { color: #0d1117; }
.mobile-date-item.today::after {
  content: ''; position: absolute; bottom: 3px; width: 4px; height: 4px;
  background: var(--accent); border-radius: 50%;
}
```

**日期条渲染规则：**
- 显示今天前后15天（共31天）
- 有报告的日子金色边框高亮
- 当前选中的日子金色背景填充
- 无报告的日子变灰（opacity: 0.3）且不可点击
- 切换报告时自动滚动居中

### 5.4 iframe 加载策略

**禁止**使用 `display: none` 或 `visibility: hidden` 隐藏 iframe，这会导致移动端滚动失效。

**正确做法：** iframe 始终可见，用 loading 遮罩层覆盖：

```javascript
function loadReport(date) {
  loading.style.display = 'flex';  // 显示遮罩
  // iframe 始终可见，不需要隐藏
  frame.src = ARCHIVE_PATH + report.filename;
  frame.onload = () => {
    loading.style.display = 'none';  // 隐藏遮罩，iframe 显示出来
  };
  // 5秒超时兜底
  setTimeout(() => { loading.style.display = 'none'; }, 5000);
}
```

```css
.loading {
  position: absolute; inset: 0; display: flex; flex-direction: column;
  align-items: center; justify-content: center; color: var(--text-muted); z-index: 10;
}
```

### 5.5 旧报告兼容性注入

对于没有移动端样式的旧报告（2026-07-10 之前的），viewer 加载时通过 iframe 注入完整样式：

```javascript
frame.onload = () => {
  try {
    const doc = frame.contentDocument || frame.contentWindow.document;
    if (doc && !doc.getElementById('mobile-header-fix')) {
      const style = doc.createElement('style');
      style.id = 'mobile-header-fix';
      style.textContent = `@media (max-width: 600px) {
        body { overflow-y: auto !important; -webkit-overflow-scrolling: touch !important; }
        .container { padding: 12px !important; }
        header { display: flex !important; flex-direction: row !important; flex-wrap: nowrap !important; align-items: baseline !important; padding: 8px 0 !important; margin-bottom: 8px !important; border-bottom: 1px solid #30363d !important; }
        h1 { font-size: 15px !important; margin: 0 !important; margin-right: 8px !important; white-space: nowrap !important; flex-shrink: 0 !important; }
        .subtitle { font-size: 11px !important; color: #8b949e !important; margin: 0 !important; white-space: nowrap !important; overflow: hidden !important; text-overflow: ellipsis !important; }
        .controls { display: none !important; }
        .filter-bar { display: none !important; }
        .cards-container { margin-top: 0 !important; }
        .card { margin-bottom: 10px !important; border-radius: 8px !important; }
        .card-header { padding: 10px 12px !important; flex-direction: column !important; align-items: flex-start !important; gap: 6px !important; }
        .card-header::after { align-self: flex-end !important; margin-top: -20px !important; }
        .card-title { gap: 6px !important; }
        .stars { font-size: 14px !important; }
        .product-name { font-size: 14px !important; }
        .score { font-size: 16px !important; }
        .card-tags { gap: 4px !important; }
        .tag { padding: 2px 8px !important; font-size: 11px !important; }
        .card-quote { gap: 6px !important; }
        .price { font-size: 16px !important; }
        .change { font-size: 13px !important; padding: 1px 6px !important; }
        .card-body { padding: 0 12px !important; }
        .card.expanded .card-body { padding: 0 12px 12px !important; }
        .quick-info { grid-template-columns: repeat(3, 1fr) !important; gap: 8px !important; padding: 10px 0 !important; margin-bottom: 10px !important; }
        .info-label { font-size: 11px !important; }
        .info-value { font-size: 13px !important; }
        .summary { padding: 8px 12px !important; font-size: 13px !important; margin-bottom: 10px !important; }
        .section { margin-bottom: 10px !important; }
        .section-title { font-size: 12px !important; margin-bottom: 6px !important; }
        .logic-item { padding: 6px 0 !important; font-size: 13px !important; }
        .risk-item { padding: 6px 10px !important; font-size: 12px !important; margin-bottom: 4px !important; }
        .quant-grid { grid-template-columns: repeat(3, 1fr) !important; gap: 8px !important; }
        .quant-item { padding: 8px !important; }
        .quant-label { font-size: 11px !important; }
        .quant-value { font-size: 14px !important; }
        .sector-info { font-size: 13px !important; }
        .sector-avg { font-size: 13px !important; padding: 6px 10px !important; }
        .stocks-list { grid-template-columns: repeat(2, 1fr) !important; gap: 6px !important; }
        .stock-item { padding: 6px 10px !important; font-size: 12px !important; }
        footer { padding: 12px 0 !important; margin-top: 12px !important; font-size: 11px !important; }
      }`;
      doc.head.appendChild(style);
    }
  } catch(e) {}
};
```

**注意：** 注入样式必须与 generator.py 的 @media 规则**逐行对应**，不能遗漏任何选择器。

---

## 6. report_list.html 历史总览规范

### 6.1 移动端适配 (@media max-width: 640px)

```css
@media (max-width: 640px) {
  .container { padding: 10px; }
  .header { flex-direction: column; align-items: flex-start; gap: 10px; padding: 14px 0 12px; }
  .header-left { width: 100%; }
  .header-title { font-size: 16px; }
  .btn-back { font-size: 12px; padding: 6px 12px; }
  .search-bar { margin-bottom: 12px; }
  .search-box input { font-size: 14px; padding: 10px 12px 10px 36px; }
  .stats-bar { gap: 8px; }
  .stat-card { min-width: 0; flex: 1 1 calc(50% - 4px); padding: 10px 12px; }
  .stat-value { font-size: 18px; }
  .report-item { flex-wrap: wrap; gap: 8px; padding: 10px 12px; }
  .date-badge { min-width: 44px; padding: 5px 8px; }
  .date-day { font-size: 15px; }
  .report-info { width: 100%; order: 3; }
  .report-title { font-size: 14px; margin-bottom: 4px; }
  .report-meta { gap: 4px; }
  .meta-tag { font-size: 11px; padding: 2px 8px; }
  .count-pills { order: 2; }
  .count-pill { font-size: 11px; padding: 3px 8px; }
  .btn-view { order: 4; width: 100%; justify-content: center; padding: 8px; font-size: 13px; }
  .pagination { gap: 4px; }
  .page-btn { min-width: 32px; height: 32px; font-size: 13px; }
}
```

---

## 7. 交互脚本 (JavaScript)

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

## 8. 文件输出规范

1. **主文件**：`output/index.html`（当日报告）
2. **归档文件**：`archive/YYYY-MM-DD.html`（历史归档）
3. **索引文件**：生成后必须调用 `build_index.py` 更新 `report_index.json`

---

## 9. 修改记录

| 日期 | 修改内容 |
|------|----------|
| 2026-07-10 | **Phase 3 分析层升级**：新增新闻舆情监控（华尔街见闻NLP情绪分析）、宏观数据摘要（CPI/PPI/PMI/LPR/M2/汇率/准备金率）、历史价格分位图（近1年/3年分位+均线趋势） |
| 2026-07-10 | **数据源真实化**：fetcher.py v2.0 统一新浪期货API + akshare备用，10个品种全部接入真实行情（PS多晶硅通过akshare CF市场） |
| 2026-07-10 | **流水线扩展**：main.py 6步流水线（行情→新闻→宏观→分析→生成→推送） |
| 2026-07-10 | iframe 加载策略：iframe 始终可见，用 loading 遮罩层覆盖，避免移动端初始滚动失效 |
| 2026-07-10 | iframe 注入旧报告样式：完整 @media 规则（含 .card / .quick-info / .quant-grid / .stocks-list / footer 等全部选择器） |
| 2026-07-10 | body 添加 `overflow-y: auto; -webkit-overflow-scrolling: touch;` |
| 2026-07-10 | 添加 report_viewer.html（移动端顶部日期条 + toolbar 隐藏）和 report_list.html |
| 2026-07-10 | 添加完整移动端 @media 样式，header 改为 flex row，隐藏 controls/filter-bar |

---

## 10. 新增模块规范（Phase 3）

### 10.1 新闻舆情监控（news_analyzer.py）

**数据源**：华尔街见闻 API (`api.wallstreetcn.com/apiv1/content/lives`)

**分析逻辑**：
- 抓取近24小时50条要闻
- 通过品种关键词匹配（PRODUCT_KEYWORDS 映射表）
- 情感词典分析（正/负面词库），输出 sentiment ∈ [-1, +1]
- 标签：乐观(>0.2) / 中性 / 悲观(<-0.2)

**输出**：`data/news_sentiment_YYYYMMDD.json`

**报告展示**：每个品种卡片内新增 "📰 舆情监控（近24h）" section

---

### 10.2 宏观数据（macro_data.py）

**数据源**：akshare + 新浪汇率API

**指标列表**：CPI同比、PPI同比、制造业PMI、USD/CNY、1年期LPR、M2同比、存款准备金率

**品种-宏观映射**：
- 有色(CU/PB)：PMI + 汇率
- 能源化工(SC/SA)：PPI + M2
- 黑色(RB/I)：PMI
- 农产品(M/RM/P)：CPI

**输出**：`data/macro_YYYYMMDD.json`

**报告展示**：controls 下方新增 "📊 宏观环境速览" 横幅

---

### 10.3 历史价格分位（history_tracker.py）

**数据存储**：`data/history/{CODE}_history.json`（每日追加）

**计算指标**：近1年分位、近3年分位、20日/60日均线、20日波动率、均线趋势

**评分权重**：价格位置评分优先使用动态1年分位

**报告展示**：每个品种卡片内新增 "📊 历史价格分位" section

---

### 10.4 评分模型 v2.0（analyzer.py）

**权重调整**：
| 维度 | 旧权重 | 新权重 |
|------|--------|--------|
| 价格位置 | 20% | 20% |
| 动量趋势 | 20% | 20% |
| 基本面 | 30% | 20% |
| 宏观环境 | 20% | 15% |
| **新闻情绪** | - | **15%** |
| 资金流向 | 10% | 10% |

---

## 11. 流水线步骤

```
[1/6] 抓取行情数据    → fetcher.py
[2/6] 抓取新闻舆情    → news_analyzer.py
[3/6] 抓取宏观数据    → macro_data.py
[4/6] 执行AI分析      → analyzer.py
[5/6] 生成HTML报告    → generator.py
[6/6] 推送报告        → pusher.py
```

**定时**：工作日 16:30
