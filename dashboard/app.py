#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
舆情监控仪表盘 - Streamlit Cloud + Supabase

部署到 Streamlit Cloud:
1. 推送代码到 GitHub
2. 在 https://streamlit.io/cloud 创建应用
3. 配置 Secrets (SUPABASE_URL, SUPABASE_KEY)
4. 启动应用

本地测试:
    cd dashboard
    streamlit run app.py
"""
import os
import sys
from pathlib import Path
from datetime import datetime

import streamlit as st
import pandas as pd
import plotly.express as px
import requests

# ==================== 配置管理 ====================

# ==================== 配置管理 ====================

# 加载配置（兼容本地和云端）
# 云端：从 st.secrets 读取
# 本地：从环境变量读取

try:
    # 尝试从 Streamlit secrets 获取（云端部署）
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except:
    # 本地开发：从环境变量获取
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# 验证配置
if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("❌ 缺少 Supabase 配置")
    st.info("""
    **请在以下位置配置：**
    
    **Streamlit Cloud 部署：**
    - 管理页面 → Settings → Secrets
    - 添加 SUPABASE_URL 和 SUPABASE_KEY
    
    **本地开发：**
    - 在项目根目录创建 .env 文件
    - 添加 SUPABASE_URL=xxx 和 SUPABASE_KEY=xxx
    """)
    st.stop()

# 显示配置状态（调试用，可删除）
# st.sidebar.write("✅ Supabase 已配置")
# st.sidebar.write(f"URL: {SUPABASE_URL[:30]}...")

# ==================== 页面配置 ====================

st.set_page_config(
    page_title="舆情监控仪表盘",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📊 舆情监控仪表盘")
st.caption(f"最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.markdown("---")


# ==================== 数据获取 ====================

@st.cache_data(ttl=60)
def load_data(limit: int = 100):
    """从 Supabase 加载数据"""
    try:
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"
        }
        
        params = {
            "select": "*",
            "order": "last_modify_ts.desc",
            "limit": limit
        }
        
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/xhs_notes",
            headers=headers,
            params=params,
            timeout=15
        )
        
        if resp.status_code == 200:
            data = resp.json()
            return pd.DataFrame(data)
        else:
            st.error(f"数据加载失败: {resp.text}")
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f"数据加载异常: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=300)
def get_stats():
    """获取统计数据"""
    try:
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
        }
        
        # 获取总数
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/xhs_notes",
            headers=headers,
            params={"select": "sentiment"},
            timeout=10
        )
        
        if resp.status_code == 200:
            data = resp.json()
            from collections import Counter
            sentiments = [note.get('sentiment', 'unknown') for note in data]
            return {
                'total': len(data),
                'sentiment_counts': dict(Counter(sentiments))
            }
        
        return {'total': 0, 'sentiment_counts': {}}
        
    except Exception as e:
        st.error(f"统计异常: {e}")
        return {'total': 0, 'sentiment_counts': {}}


# ==================== 侧边栏 ====================

with st.sidebar:
    st.header("⚙️ 控制面板")
    
    # 刷新按钮
    if st.button("🔄 立即刷新"):
        st.cache_data.clear()
        st.rerun()
    
    # 自动刷新
    auto_refresh = st.checkbox("自动刷新 (60秒)", value=False)
    
    st.markdown("---")
    
    # 筛选
    st.header("🔍 筛选")
    
    sentiment_filter = st.multiselect(
        "情感倾向",
        options=["positive", "neutral", "negative"],
        default=["positive", "neutral", "negative"]
    )
    
    keyword_filter = st.text_input("关键词搜索", "")
    
    st.markdown("---")
    
    # 关于
    st.header("ℹ️ 关于")
    st.markdown("""
    **舆情监控系统**
    
    - 实时爬取小红书数据
    - AI 情感分析
    - 负面舆情告警
    - 数据可视化
    """)


# ==================== 主内容 ====================

# 加载数据
df = load_data()
stats = get_stats()

if df.empty:
    st.warning("📭 暂无数据")
    st.info("请先运行爬虫收集数据")
    st.stop()

# 应用筛选
if sentiment_filter and 'sentiment' in df.columns:
    df = df[df['sentiment'].isin(sentiment_filter)]

if keyword_filter:
    mask = (
        df['title'].astype(str).str.contains(keyword_filter, na=False, case=False) |
        df['desc'].astype(str).str.contains(keyword_filter, na=False, case=False)
    )
    df = df[mask]

# ==================== 指标卡 ====================

st.header("📈 核心指标")

cols = st.columns(4)

with cols[0]:
    st.metric("总笔记数", stats['total'])

with cols[1]:
    neg_count = stats['sentiment_counts'].get('negative', 0)
    neg_percent = f"{neg_count/stats['total']*100:.1f}%" if stats['total'] > 0 else "0%"
    st.metric("负面舆情", neg_count, delta=neg_percent, delta_color="inverse")

with cols[2]:
    pos_count = stats['sentiment_counts'].get('positive', 0)
    st.metric("正面评价", pos_count)

with cols[3]:
    if 'source_keyword' in df.columns:
        keywords = df['source_keyword'].nunique()
        st.metric("监控关键词", keywords)

st.markdown("---")

# ==================== 可视化 ====================

st.header("📊 数据分析")

col1, col2 = st.columns(2)

with col1:
    # 情感分布
    if 'sentiment' in df.columns:
        sentiment_counts = df['sentiment'].value_counts()
        
        colors = {
            'positive': '#52c41a',
            'neutral': '#faad14', 
            'negative': '#f5222d'
        }
        
        fig = px.pie(
            values=sentiment_counts.values,
            names=sentiment_counts.index,
            title="情感分布",
            color=sentiment_counts.index,
            color_discrete_map=colors
        )
        st.plotly_chart(fig, use_container_width=True)

with col2:
    # 关键词 TOP10
    if 'source_keyword' in df.columns:
        keyword_counts = df['source_keyword'].value_counts().head(10)
        
        fig = px.bar(
            x=keyword_counts.values,
            y=keyword_counts.index,
            orientation='h',
            title="Top 10 关键词",
            labels={'x': '数量', 'y': '关键词'}
        )
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ==================== 负面告警 ====================

st.header("🚨 负面舆情监控")

if 'sentiment' in df.columns:
    negative_df = df[df['sentiment'] == 'negative']
    
    if not negative_df.empty:
        st.error(f"⚠️ 发现 {len(negative_df)} 条负面舆情！")
        
        for idx, row in negative_df.head(5).iterrows():
            with st.expander(f"📌 {row.get('title', '无标题')[:40]}..."):
                st.markdown(f"**标题:** {row.get('title', '无')}")
                st.markdown(f"**内容:** {str(row.get('desc', '无'))[:150]}...")
                st.markdown(f"**关键词:** {row.get('source_keyword', '无')}")
                st.markdown(f"**点赞:** {row.get('liked_count', 0)}")
                if row.get('note_url'):
                    st.markdown(f"[🔗 查看原文]({row['note_url']})")
    else:
        st.success("✅ 暂无负面舆情，一切正常！")

st.markdown("---")

# ==================== 数据表格 ====================

st.header("📋 详细数据")

# 选择列
display_cols = ['title', 'sentiment', 'liked_count', 'source_keyword', 'note_url']
available_cols = [c for c in display_cols if c in df.columns]

display_df = df[available_cols].copy()

# 截断文本
if 'title' in display_df.columns:
    display_df['title'] = display_df['title'].astype(str).str[:50] + '...'

st.dataframe(display_df, use_container_width=True, hide_index=True)

# ==================== 自动刷新 ====================

if auto_refresh:
    st.markdown("---")
    st.info("🔄 自动刷新中...")
    
    import time
    time.sleep(60)
    st.rerun()

# ==================== 页脚 ====================

st.markdown("---")
st.caption("🚀 Powered by Streamlit Cloud + Supabase")
