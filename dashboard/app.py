#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
舆情监控仪表盘 - Streamlit Cloud + Supabase
优化版：基于实际字段设计
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from datetime import datetime, timedelta
from collections import Counter

# 页面配置
st.set_page_config(
    page_title="舆情监控仪表盘",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 读取 Secrets
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

# ==================== 数据加载 ====================

@st.cache_data(ttl=60)
def load_data():
    """从 Supabase 加载数据"""
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/xhs_notes",
        headers=headers,
        params={"select": "*", "limit": 1000},
        timeout=15
    )
    
    if resp.status_code == 200:
        df = pd.DataFrame(resp.json())
        # 数据类型转换
        if 'publish_time' in df.columns:
            df['publish_time'] = pd.to_datetime(df['publish_time'])
        if 'created_at' in df.columns:
            df['created_at'] = pd.to_datetime(df['created_at'])
        if 'liked_count' in df.columns:
            df['liked_count'] = pd.to_numeric(df['liked_count'], errors='coerce').fillna(0)
        if 'comment_count' in df.columns:
            df['comment_count'] = pd.to_numeric(df['comment_count'], errors='coerce').fillna(0)
        return df
    return pd.DataFrame()

# ==================== 侧边栏 ====================

with st.sidebar:
    st.title("📊 舆情监控")
    
    # 刷新按钮
    if st.button("🔄 刷新数据"):
        st.cache_data.clear()
        st.rerun()
    
    st.markdown("---")
    
    # 筛选条件
    st.header("🔍 筛选")
    
    # 时间范围
    time_range = st.selectbox(
        "时间范围",
        ["全部", "最近7天", "最近30天", "最近90天"]
    )
    
    # 情感筛选
    sentiment_filter = st.multiselect(
        "情感倾向",
        options=["positive", "neutral", "negative"],
        default=["positive", "neutral", "negative"]
    )
    
    # 关键词搜索
    keyword_search = st.text_input("关键词搜索", "")
    
    # IP 位置筛选
    ip_filter = st.text_input("地区筛选", "")
    
    st.markdown("---")
    st.caption(f"⏰ 更新时间: {datetime.now().strftime('%H:%M:%S')}")

# ==================== 加载并筛选数据 ====================

df = load_data()

if df.empty:
    st.error("❌ 暂无数据，请先运行爬虫")
    st.stop()

# 应用筛选
if time_range != "全部" and 'publish_time' in df.columns:
    days = {"最近7天": 7, "最近30天": 30, "最近90天": 90}[time_range]
    cutoff = datetime.now() - timedelta(days=days)
    df = df[df['publish_time'] >= cutoff]

if sentiment_filter and 'sentiment' in df.columns:
    df = df[df['sentiment'].isin(sentiment_filter)]

if keyword_search:
    mask = (
        df['title'].astype(str).str.contains(keyword_search, case=False, na=False) |
        df['desc'].astype(str).str.contains(keyword_search, case=False, na=False)
    )
    df = df[mask]

if ip_filter and 'ip_location' in df.columns:
    df = df[df['ip_location'].astype(str).str.contains(ip_filter, case=False, na=False)]

# ==================== 顶部指标卡 ====================

st.title("📈 舆情概览")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("总笔记数", len(df))

with col2:
    if 'sentiment' in df.columns:
        neg = len(df[df['sentiment'] == 'negative'])
        st.metric("负面舆情", neg, delta=f"{neg/len(df)*100:.1f}%" if len(df) > 0 else "0%", delta_color="inverse")

with col3:
    if 'sentiment' in df.columns:
        pos = len(df[df['sentiment'] == 'positive'])
        st.metric("正面评价", pos)

with col4:
    if 'liked_count' in df.columns:
        total_likes = int(df['liked_count'].sum())
        st.metric("总点赞", f"{total_likes:,}")

with col5:
    if 'source_keyword' in df.columns:
        keywords = df['source_keyword'].nunique()
        st.metric("监控关键词", keywords)

st.markdown("---")

# ==================== 可视化区域 ====================

st.header("📊 数据分析")

col_left, col_right = st.columns(2)

# 情感分布饼图
with col_left:
    if 'sentiment' in df.columns:
        sentiment_counts = df['sentiment'].value_counts()
        colors = {'positive': '#52c41a', 'neutral': '#faad14', 'negative': '#f5222d'}
        
        fig = px.pie(
            values=sentiment_counts.values,
            names=sentiment_counts.index,
            title="情感分布",
            color=sentiment_counts.index,
            color_discrete_map=colors,
            hole=0.4
        )
        fig.update_traces(textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)

# 关键词 TOP10
with col_right:
    if 'source_keyword' in df.columns:
        keyword_counts = df['source_keyword'].value_counts().head(10)
        
        fig = px.bar(
            x=keyword_counts.values,
            y=keyword_counts.index,
            orientation='h',
            title="Top 10 关键词",
            labels={'x': '数量', 'y': '关键词'},
            color=keyword_counts.values,
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig, use_container_width=True)

# 第二行可视化
col_left2, col_right2 = st.columns(2)

# 地区分布
with col_left2:
    if 'ip_location' in df.columns:
        ip_counts = df['ip_location'].value_counts().head(10)
        fig = px.bar(
            x=ip_counts.values,
            y=ip_counts.index,
            orientation='h',
            title="地区分布 Top 10",
            labels={'x': '数量', 'y': '地区'}
        )
        st.plotly_chart(fig, use_container_width=True)

# 点赞数分布
with col_right2:
    if 'liked_count' in df.columns:
        fig = px.histogram(
            df[df['liked_count'] <= 100],  # 过滤极端值
            x='liked_count',
            nbins=20,
            title="点赞数分布（0-100）",
            labels={'liked_count': '点赞数', 'count': '笔记数'}
        )
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ==================== 负面舆情告警 ====================

st.header("🚨 负面舆情监控")

if 'sentiment' in df.columns:
    negative_df = df[df['sentiment'] == 'negative'].sort_values('liked_count', ascending=False)
    
    if not negative_df.empty:
        st.error(f"⚠️ 发现 {len(negative_df)} 条负面舆情")
        
        for idx, row in negative_df.head(5).iterrows():
            with st.expander(f"📌 {row.get('title', '无标题')[:50]}... | 👍 {row.get('liked_count', 0)}"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**标题:** {row.get('title', '无')}")
                    st.markdown(f"**内容:** {str(row.get('desc', ''))[:200]}...")
                    st.markdown(f"**作者:** {row.get('nickname', '未知')} | **地区:** {row.get('ip_location', '未知')}")
                    st.markdown(f"**关键词:** {row.get('source_keyword', '无')}")
                    st.markdown(f"**点赞:** {row.get('liked_count', 0)} | **评论:** {row.get('comment_count', 0)}")
                
                with col2:
                    if row.get('note_url'):
                        st.markdown(f"[🔗 查看原文]({row['note_url']})")
                    if row.get('publish_time'):
                        st.caption(f"发布时间: {row['publish_time'][:10]}")
    else:
        st.success("✅ 暂无负面舆情，一切正常！")

st.markdown("---")

# ==================== 数据表格 ====================

st.header("📋 详细数据")

# 选择显示列
display_cols = ['title', 'sentiment', 'liked_count', 'comment_count', 'ip_location', 'source_keyword', 'note_url']
available_cols = [c for c in display_cols if c in df.columns]

display_df = df[available_cols].copy()

# 截断长文本
if 'title' in display_df.columns:
    display_df['title'] = display_df['title'].astype(str).str[:60] + '...'

# 添加链接
if 'note_url' in display_df.columns:
    display_df['note_url'] = display_df['note_url'].apply(lambda x: f"[链接]({x})" if x else "")

st.dataframe(display_df, use_container_width=True, hide_index=True)

# 导出功能
st.download_button(
    label="📥 导出数据 (CSV)",
    data=df.to_csv(index=False).encode('utf-8'),
    file_name=f"舆情数据_{datetime.now().strftime('%Y%m%d')}.csv",
    mime='text/csv'
)

# ==================== 页脚 ====================

st.markdown("---")
st.caption("🚀 Powered by Streamlit Cloud + Supabase | 舆情监控系统")
