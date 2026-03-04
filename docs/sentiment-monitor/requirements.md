# Sentiment Monitor 需求文档

> 基于 MediaCrawler 的舆情监控与情感分析系统

---

## 1. 项目背景与目标

### 1.1 背景
基于 MediaCrawler 多平台爬虫能力，复用已验证的技术方案（Supabase + Streamlit + 百度NLP），构建舆情监控与情感分析系统。

### 1.2 目标
- 自动化监控指定关键词在小红书平台的内容
- 百度 NLP 情感分析（正/中/负三分类）
- Streamlit 数据看板展示
- 负面舆情钉钉/企微告警

---

## 2. 功能需求

### 2.1 数据采集模块
| 功能 | 优先级 | 说明 |
|------|--------|------|
| 关键词监控 | P0 | 配置关键词列表，自动搜索采集 |
| 小红书平台 | P0 | 首期只支持小红书 |
| 定时采集 | P0 | 每小时执行一次 |
| 去重入库 | P0 | 每次约20条，去重后插入 Supabase |
| 增量采集 | P1 | 只采集上次之后的新内容 |
| 多平台扩展 | P2 | 后续支持抖音、微博 |

### 2.2 情感分析模块
| 功能 | 优先级 | 说明 |
|------|--------|------|
| 三分类情感 | P0 | 正面 / 中性 / 负面（百度 NLP） |
| 置信度分数 | P0 | 百度 API 返回的置信度 |
| 批量分析 | P0 | 新采集内容自动分析 |

> **技术决策**: SnowNLP 效果不理想，采用百度 NLP API

### 2.3 数据存储
| 功能 | 优先级 | 说明 |
|------|--------|------|
| Supabase 存储 | P0 | 复用已有方案，PostgreSQL 云端数据库 |
| 数据模型 | P0 | 笔记内容 + 情感分析结果 |
| 历史数据 | P1 | 定期清理或归档 |

### 2.4 告警通知
| 功能 | 优先级 | 说明 |
|------|--------|------|
| 负面舆情告警 | P0 | 检测到负面内容时触发 |
| 告警阈值 | P0 | 需测试后确定（参考值：负面置信度>0.7） |
| 钉钉通知 | P0 | Webhook 方式 |
| 企业微信 | P1 | 后续支持 |

### 2.5 数据看板
| 功能 | 优先级 | 说明 |
|------|--------|------|
| Streamlit 看板 | P0 | 复用已有方案，解决分发问题 |
| 核心指标 | P0 | 今日新增、负面占比、趋势图 |
| 笔记列表 | P0 | 搜索、筛选、导出 |
| 告警记录 | P1 | 历史告警查询 |

> **暂不开发 Web UI**，关键词管理通过配置文件或数据库直接操作

---

## 3. 技术方案（已确定）

| 模块 | 方案 |
|------|------|
| 爬虫引擎 | MediaCrawler + Playwright |
| 采集调度 | APScheduler（本地）/ GitHub Actions（云端） |
| 情感分析 | **百度 NLP API** |
| 数据库 | **Supabase (PostgreSQL)** |
| 看板 | **Streamlit** |
| 告警 | 钉钉 Webhook |

---

## 4. 数据模型

### 4.1 笔记内容 (contents)
```sql
id: bigint primary key
content_id: varchar unique -- 小红书笔记ID
keyword: varchar -- 监控关键词
title: text -- 标题
content: text -- 正文
author: varchar -- 作者
url: varchar -- 链接
likes: int -- 点赞数
comments: int -- 评论数
shares: int -- 分享数
publish_time: timestamp -- 发布时间
collected_at: timestamp -- 采集时间
```

### 4.2 情感分析 (sentiments)
```sql
id: bigint primary key
content_id: bigint ref contents(id)
sentiment: varchar -- positive/neutral/negative
confidence: float -- 置信度 0-1
analyzed_at: timestamp -- 分析时间
```

### 4.3 告警记录 (alerts)
```sql
id: bigint primary key
content_id: bigint ref contents(id)
alert_type: varchar -- negative/burst
severity: varchar -- high/medium/low
message: text -- 告警内容
is_resolved: boolean -- 是否处理
created_at: timestamp
```

---

## 5. 里程碑规划

| 阶段 | 目标 | 时间 |
|------|------|------|
| MVP | 小红书采集 + 百度NLP + Supabase + 基础告警 | 1 周 |
| V1.0 | Streamlit 看板 + 钉钉告警 + 阈值调优 | 2 周 |
| V1.5 | 多关键词管理 + 数据导出 + 定时任务优化 | 3 周 |

---

## 6. 配置项

```yaml
# config/sentiment_monitor.yaml

keywords:                     # 监控关键词列表
  - "航空食品"
  - "飞机餐"

platform: xhs                 # 平台：xhs（首期）

schedule:
  interval: 3600              # 采集间隔（秒），默认1小时
  max_notes: 20               # 每次最大采集数

baidu_nlp:
  api_key: ""                 # 百度 API Key
  secret_key: ""              # 百度 Secret Key

supabase:
  url: ""                     # Supabase URL
  key: ""                     # Supabase Key

alert:
  negative_threshold: 0.7     # 负面告警阈值（置信度）
  dingtalk_webhook: ""        # 钉钉 Webhook
```

---

*文档创建时间: 2026-03-03*  
*最后更新: 2026-03-03*
