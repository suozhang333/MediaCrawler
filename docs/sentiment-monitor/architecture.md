# Sentiment Monitor 架构设计

> 技术架构与模块设计文档

---

## 1. 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      用户界面层 (Web UI)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   仪表盘      │  │  配置管理     │  │  数据查询     │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                      API 服务层 (FastAPI)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  监控任务 API │  │  情感分析 API │  │  数据查询 API │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
┌───────▼─────┐ ┌────▼────┐ ┌────▼────┐
│  爬虫调度器   │ │ 情感分析 │ │ 告警通知 │
│ (APScheduler)│ │  引擎    │ │  模块    │
└───────┬─────┘ └────┬────┘ └────┬────┘
        │            │            │
┌───────▼────────────▼────────────▼─────┐
│           数据存储层                   │
│  ┌──────────┐ ┌──────────┐ ┌────────┐ │
│  │  SQLite  │ │  MySQL   │ │  Cache │ │
│  │ (开发)   │ │ (生产)   │ │ (Redis)│ │
│  └──────────┘ └──────────┘ └────────┘ │
└─────────────────────────────────────────┘
```

---

## 2. 模块设计

### 2.1 爬虫调度模块
```
sentiment_monitor/
├── scheduler/
│   ├── __init__.py
│   ├── task_manager.py      # 任务管理
│   ├── job_config.py        # 任务配置
│   └── executor.py          # 执行器
```

### 2.2 情感分析模块
```
sentiment_monitor/
├── analyzer/
│   ├── __init__.py
│   ├── base.py              # 抽象基类
│   ├── baidu_nlp.py         # 百度 NLP 实现
│   ├── local_model.py       # 本地模型实现
│   └── aggregator.py        # 结果聚合
```

### 2.3 告警通知模块
```
sentiment_monitor/
├── notifier/
│   ├── __init__.py
│   ├── base.py              # 抽象基类
│   ├── wechat_work.py       # 企业微信
│   ├── dingtalk.py          # 钉钉
│   └── email.py             # 邮件
```

### 2.4 数据存储模块
```
sentiment_monitor/
├── storage/
│   ├── __init__.py
│   ├── models.py            # 数据模型
│   ├── repository.py        # 数据访问
│   └── migration.py         # 数据库迁移
```

---

## 3. 数据模型

### 3.1 监控任务 (MonitorTask)
```python
class MonitorTask:
    id: int
    name: str                  # 任务名称
    platform: str              # 平台 (xhs/dy/wb)
    monitor_type: str          # 类型 (keyword/creator)
    targets: List[str]         # 监控目标
    frequency: int             # 采集频率(分钟)
    is_active: bool            # 是否启用
    created_at: datetime
    updated_at: datetime
```

### 3.2 采集内容 (Content)
```python
class Content:
    id: int
    task_id: int               # 关联任务
    platform: str              # 平台
    content_id: str            # 平台内容ID
    author: str                # 作者
    title: str                 # 标题
    content: str               # 内容
    url: str                   # 链接
    publish_time: datetime     # 发布时间
    likes: int                 # 点赞数
    comments: int              # 评论数
    shares: int                # 分享数
    collected_at: datetime     # 采集时间
```

### 3.3 情感分析结果 (SentimentResult)
```python
class SentimentResult:
    id: int
    content_id: int            # 关联内容
    sentiment: str             # 情感类型 (positive/negative/neutral)
    confidence: float          # 置信度
    score: float               # 情感分数 (-1 ~ 1)
    aspects: List[Aspect]      # 细粒度情感
    analyzed_at: datetime      # 分析时间
```

### 3.4 告警记录 (Alert)
```python
class Alert:
    id: int
    alert_type: str            # 告警类型
    severity: str              # 严重级别
    content_id: int            # 关联内容
    message: str               # 告警消息
    is_resolved: bool          # 是否已处理
    created_at: datetime
```

---

## 4. 接口设计

### 4.1 监控任务管理
```
GET    /api/v1/tasks          # 获取任务列表
POST   /api/v1/tasks          # 创建任务
GET    /api/v1/tasks/{id}     # 获取任务详情
PUT    /api/v1/tasks/{id}     # 更新任务
DELETE /api/v1/tasks/{id}     # 删除任务
POST   /api/v1/tasks/{id}/run # 立即执行
```

### 4.2 数据查询
```
GET /api/v1/contents          # 内容列表（支持筛选）
GET /api/v1/sentiments        # 情感分析结果
GET /api/v1/trends            # 情感趋势数据
GET /api/v1/statistics        # 统计数据
```

### 4.3 告警管理
```
GET  /api/v1/alerts           # 告警列表
PUT  /api/v1/alerts/{id}      # 处理告警
```

---

## 5. 配置设计

```yaml
# config/sentiment_monitor.yaml

# 监控配置
monitor:
  default_frequency: 30       # 默认采集频率(分钟)
  max_tasks_per_platform: 10  # 每平台最大任务数
  
# 情感分析配置
analyzer:
  provider: baidu_nlp         # 提供商: baidu_nlp / local
  api_key: ""                 # API 密钥
  secret_key: ""              # 密钥
  
# 告警配置
alert:
  negative_threshold: 0.7     # 负面阈值
  burst_threshold: 1000       # 爆发阈值(互动量)
  
# 通知配置
notification:
  channels:
    - type: wechat_work
      webhook_url: ""
    - type: dingtalk
      webhook_url: ""
```

---

*文档创建时间: 2026-03-03*
