#!/bin/bash
cd /root/.openclaw/workspace/futures-daily
git add -A
git commit -m "feat: 数据守护者模块 - 严格陈旧数据检测 + 自动报警

- 新增 scripts/data_guardian.py 数据质量守护模块
- 检测维度：
  1. 单日陈旧（close/change_pct/volume/open_interest 全部与昨日相同）
  2. 连续多天陈旧（连续N天数据指纹相同）
  3. 数据冻结（change_pct=0 但 volume>0）
  4. Mock 降级检测
  5. 大面积异常（>50%品种异常自动CRITICAL报警）
- 报警机制：
  - 飞书消息自动推送（复用 stock-assistant 凭证）
  - 报警去重（24h冷却期，同一问题不重复骚扰）
  - 报警级别：WARNING / CRITICAL
- 流水线集成：main.py 中 1.5 步骤自动检测
- 阈值控制：>70%异常自动中止流水线，>50%异常继续但报警
- config.json 新增 data_guardian 配置段

历史数据回溯验证：
- 7月14日 vs 7月13日：8/10 品种陈旧（检测到用户之前发现的问题）
- 7月15日 vs 7月14日：0/10 品种陈旧（数据新鲜）"
git push origin main
