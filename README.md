# 期货基本面日报系统

基于 PRD v1.0 构建，覆盖 10 个期货品种的基本面分析日报。

## 项目结构

```
futures-daily/
├── config.json              # 配置文件
├── scripts/
│   ├── main.py              # 主控脚本（一键执行）
│   ├── fetcher.py           # 数据抓取（新浪期货API）
│   ├── analyzer.py          # AI分析引擎（规则评分系统）
│   ├── generator.py         # HTML报告生成
│   └── pusher.py            # GitHub推送
├── .github/workflows/
│   └── daily.yml            # GitHub Actions定时任务
├── data/                    # 原始数据存档
├── analysis/                # 分析结果存档
├── output/                  # 生成的HTML报告
├── archive/                 # 历史报告归档
├── requirements.txt
└── README.md
```

## 使用方法

### 本地测试（模拟数据）

```bash
# 进入项目目录
cd futures-daily

# 运行完整流水线（模拟数据+本地模式）
python3 scripts/main.py --mock --local
```

### 生产运行（真实数据+Git推送）

```bash
# 运行完整流水线
python3 scripts/main.py
```

### 分步执行

```bash
# 1. 抓取行情数据
python3 scripts/fetcher.py

# 2. 执行AI分析
python3 scripts/analyzer.py

# 3. 生成HTML报告
python3 scripts/generator.py

# 4. 推送到GitHub
python3 scripts/pusher.py
```

## 数据源

| 维度 | 来源 |
|------|------|
| 期货行情 | 新浪期货API（主力合约） |
| 库存/仓单 | 交易所官网 + 第三方平台 |
| 现货价格 | 生意社、SMM、钢联数据 |
| 宏观数据 | 国家统计局、央行、海关总署 |
| 行业资讯 | 垂直媒体头条 |

## 品种覆盖（首期10个）

1. **多晶硅（PS）** - 新能源
2. **菜粕（RM）** - 农产品
3. **铅（PB）** - 有色金属
4. **螺纹钢（RB）** - 黑色系
5. **原油（SC）** - 能源化工
6. **豆粕（M）** - 农产品
7. **铁矿石（I）** - 黑色系
8. **铜（CU）** - 有色金属
9. **棕榈油（P）** - 农产品
10. **纯碱（SA）** - 能源化工

## 分析框架

评分维度及权重：
- **价格位置（20%）**：历史分位、估值水平
- **动量趋势（20%）**：近期涨跌、加速度
- **基本面（30%）**：库存、供需、产能、基差
- **宏观环境（20%）**：政策、利率、汇率
- **资金流向（10%）**：持仓变化、成交量

## 自动化部署

GitHub Actions 配置：
- **触发时间**：工作日 16:30（UTC+8）
- **支持手动触发**：workflow_dispatch
- **自动部署**：推送到 gh-pages 分支

## 配置说明

修改 `config.json` 可调整：
- 品种列表和权重
- 数据源配置
- 评分权重和阈值
- 视觉配色方案
- GitHub仓库信息

## 待完善事项（按PRD）

- [ ] 接入Wind/同花顺iFinD付费数据
- [ ] 增加技术指标（均线、MACD、RSI）
- [ ] 增加历史回测功能（验证评分有效性）
- [ ] 品种扩展至更多板块
- [ ] 接入LLM API提升分析准确性

## License

MIT
