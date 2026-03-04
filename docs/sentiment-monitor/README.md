# Sentiment Monitor - 舆情监控与情感分析系统

> 基于 MediaCrawler 的社交媒体舆情监控解决方案

## 🎯 项目简介

Sentiment Monitor 是基于 [MediaCrawler](https://github.com/NanmiCoder/MediaCrawler) 开发的舆情监控与情感分析系统，帮助企业/个人实时监控社交媒体上的品牌声誉、产品口碑和舆论动向。

## ✨ 核心功能

| 模块 | 功能描述 |
|------|----------|
| 📡 **智能采集** | 自动监控关键词和创作者，支持多平台定时采集 |
| 🧠 **情感分析** | AI 驱动的情感识别，区分正负面及细粒度情感 |
| 📊 **舆情可视化** | 实时仪表盘展示情感趋势、热点内容 |
| 🚨 **智能告警** | 负面舆情、异常传播自动通知 |
| 📑 **数据报告** | 自动生成舆情日报/周报 |

## 🚀 快速开始

### 环境准备
```bash
# 安装依赖
uv sync

# 安装浏览器驱动
uv run playwright install
```

### 启动监控服务
```bash
# 启动 Web 服务
uv run uvicorn api.main:app --port 8080 --reload

# 启动监控任务
uv run python -m sentiment_monitor.worker
```

## 📖 文档导航

- [需求文档](./requirements.md) - 完整功能需求清单
- [架构设计](./architecture.md) - 技术架构与模块设计
- [更新日志](./changelog.md) - 版本迭代记录

## 🛠️ 技术栈

- **爬虫引擎**: MediaCrawler + Playwright
- **情感分析**: 百度 NLP / 本地 BERT 模型
- **Web 服务**: FastAPI
- **任务调度**: APScheduler
- **数据存储**: SQLite / MySQL
- **可视化**: ECharts

---

*本项目是 MediaCrawler 的扩展分支，保留原项目所有能力*
