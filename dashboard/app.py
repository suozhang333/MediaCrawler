#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
舆情监控仪表盘 - Streamlit Cloud + Supabase
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime

# 页面配置
st.set_page_config(
    page_title="舆情监控仪表盘",
    page_icon="📊",
    layout="wide"
)

# 从 Secrets 读取配置
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

st.title("📊 舆情监控仪表盘")
st.caption(f"更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 加载数据
@st.cache_data(ttl=60)
def load_data():
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    
    # 简化查询，不使用排序（避免字段不存在问题）
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/xhs_notes",
        headers=headers,
        params={"select": "*", "limit": 100},
        timeout=15
    )
    
    if resp.status_code == 200:
        data = resp.json()
        if data:
            return pd.DataFrame(data)
    
    # 调试信息
    st.error(f"查询失败: {resp.status_code} - {resp.text[:200]}")
    return pd.DataFrame()

df = load_data()

if df.empty:
    st.warning("暂无数据")
    st.stop()

# 指标卡
col1, col2, col3 = st.columns(3)
col1.metric("总笔记数", len(df))

if 'sentiment' in df.columns:
    neg_count = len(df[df['sentiment'] == 'negative'])
    col2.metric("负面舆情", neg_count)
    
    pos_count = len(df[df['sentiment'] == 'positive'])
    col3.metric("正面评价", pos_count)

# 情感分布图
if 'sentiment' in df.columns:
    st.subheader("情感分布")
    sentiment_counts = df['sentiment'].value_counts()
    fig = px.pie(values=sentiment_counts.values, names=sentiment_counts.index)
    st.plotly_chart(fig, use_container_width=True)

# 负面舆情列表
st.subheader("🚨 负面舆情")
negative_df = df[df['sentiment'] == 'negative'] if 'sentiment' in df.columns else pd.DataFrame()

if not negative_df.empty:
    for _, row in negative_df.head(5).iterrows():
        with st.expander(f"{row.get('title', '无标题')[:40]}..."):
            st.write(f"**内容:** {str(row.get('desc', ''))[:100]}...")
            st.write(f"**关键词:** {row.get('source_keyword', '无')}")
            if row.get('note_url'):
                st.markdown(f"[查看原文]({row['note_url']})")
else:
    st.success("暂无负面舆情")

# 数据表格
st.subheader("📋 数据列表")
st.dataframe(df[['title', 'sentiment', 'source_keyword']].head(20), use_container_width=True)
