#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
舆情监控仪表盘 - Streamlit Cloud + Supabase
优化版：基于实际字段设计
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime, timedelta

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

# 加载数据
df_original = load_data()

if df_original.empty:
    st.error("❌ 暂无数据，请先运行爬虫")
    st.stop()

# ==================== 侧边栏筛选 ====================

with st.sidebar:
    st.title("📊 舆情监控")
    
    # 刷新按钮
    if st.button("🔄 刷新数据"):
        st.cache_data.clear()
        st.rerun()
    
    st.markdown("---")
    
    # 基础筛选
    st.header("🔍 筛选")
    
    # 时间范围
    time_range = st.selectbox(
        "时间范围",
        ["全部", "最近7天", "最近30天", "最近90天"]
    )
    
    # 情感筛选（中文）
    sentiment_options = {"正面": "positive", "中性": "neutral", "负面": "negative"}
    selected_sentiments = st.multiselect(
        "情感倾向",
        options=list(sentiment_options.keys()),
        default=list(sentiment_options.keys())
    )
    sentiment_filter = [sentiment_options[k] for k in selected_sentiments]
    
    # 关键词搜索
    keyword_search = st.text_input("关键词搜索", "")
    
    st.markdown("---")
    
    # 地区筛选
    st.header("📍 地区")
    
    # 中国省份列表
    china_provinces = [
        '北京', '天津', '上海', '重庆', '河北', '山西', '辽宁', '吉林', '黑龙江',
        '江苏', '浙江', '安徽', '福建', '江西', '山东', '河南', '湖北', '湖南',
        '广东', '海南', '四川', '贵州', '云南', '陕西', '甘肃', '青海', '台湾',
        '内蒙古', '广西', '西藏', '宁夏', '新疆', '香港', '澳门'
    ]
    
    # 只显示数据中存在的省份
    if 'ip_location' in df_original.columns:
        available_provinces = [p for p in china_provinces if p in df_original['ip_location'].values]
        if available_provinces:
            selected_provinces = st.multiselect(
                "中国省份",
                options=available_provinces,
                default=[]
            )
        else:
            selected_provinces = []
    else:
        selected_provinces = []
    
    # 通用地区搜索
    ip_filter = st.text_input("地区搜索", "")
    
    st.markdown("---")
    st.caption(f"⏰ 更新时间: {datetime.now().strftime('%H:%M:%S')}")

# ==================== 应用筛选 ====================

df = df_original.copy()

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

if selected_provinces and 'ip_location' in df.columns:
    df = df[df['ip_location'].isin(selected_provinces)]

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
        
        # 英文转中文
        sentiment_name_map = {'positive': '正面', 'neutral': '中性', 'negative': '负面'}
        sentiment_counts.index = sentiment_counts.index.map(sentiment_name_map)
        
        colors = {'正面': '#52c41a', '中性': '#faad14', '负面': '#f5222d'}
        
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

# 中国省份分布
with col_left2:
    if 'ip_location' in df.columns:
        china_provinces = [
            '北京', '天津', '上海', '重庆', '河北', '山西', '辽宁', '吉林', '黑龙江',
            '江苏', '浙江', '安徽', '福建', '江西', '山东', '河南', '湖北', '湖南',
            '广东', '海南', '四川', '贵州', '云南', '陕西', '甘肃', '青海', '台湾',
            '内蒙古', '广西', '西藏', '宁夏', '新疆', '香港', '澳门'
        ]
        
        china_df = df[df['ip_location'].isin(china_provinces)]
        
        if not china_df.empty:
            province_counts = china_df['ip_location'].value_counts().head(15)
            
            fig = px.bar(
                x=province_counts.values,
                y=province_counts.index,
                orientation='h',
                title="🇨🇳 中国省份分布 Top 15",
                labels={'x': '笔记数量', 'y': '省份'},
                color=province_counts.values,
                color_continuous_scale='Reds'
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
            
            china_ratio = len(china_df) / len(df) * 100
            st.caption(f"🇨🇳 中国境内: {len(china_df)} 条 ({china_ratio:.1f}%) | 覆盖 {china_df['ip_location'].nunique()} 个省份")
        else:
            st.info("暂无中国省份数据")
            
        st.subheader("🌍 全球地区分布 Top 10")
        ip_counts = df['ip_location'].value_counts().head(10)
        fig2 = px.bar(
            x=ip_counts.values,
            y=ip_counts.index,
            orientation='h',
            labels={'x': '数量', 'y': '地区'},
            color=ip_counts.values,
            color_continuous_scale='Blues'
        )
        fig2.update_layout(height=250)
        st.plotly_chart(fig2, use_container_width=True)

# 点赞数分布
with col_right2:
    if 'liked_count' in df.columns:
        fig = px.histogram(
            df[df['liked_count'] <= 100],
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
            title = row.get('title', '无标题')
            url = row.get('note_url', '')
            likes = row.get('liked_count', 0)
            
            expander_label = f"📌 {title[:50]}... | 👍 {likes}"
            
            with st.expander(expander_label):
                if url:
                    st.markdown(f"### [{title}]({url})")
                else:
                    st.markdown(f"### {title}")
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**内容:** {str(row.get('desc', ''))[:200]}...")
                    st.markdown(f"**作者:** {row.get('nickname', '未知')} | **地区:** {row.get('ip_location', '未知')}")
                    st.markdown(f"**关键词:** {row.get('source_keyword', '无')}")
                    st.markdown(f"**点赞:** {row.get('liked_count', 0)} | **评论:** {row.get('comment_count', 0)}")
                
                with col2:
                    if row.get('publish_time'):
                        st.caption(f"发布时间: {row['publish_time'][:10]}")
    else:
        st.success("✅ 暂无负面舆情，一切正常！")

st.markdown("---")

# ==================== 数据表格 ====================

st.header("📋 详细数据")

display_cols = ['title', 'sentiment', 'liked_count', 'comment_count', 'ip_location', 'source_keyword']
available_cols = [c for c in display_cols if c in df.columns]

display_df = df[available_cols].copy()

# 标题添加超链接
if 'title' in display_df.columns and 'note_url' in df.columns:
    display_df['title'] = df.apply(
        lambda row: f"[{str(row['title'])[:50]}...]({row['note_url']})" if row['note_url'] else str(row['title'])[:50] + '...',
        axis=1
    )

# 情感翻译
if 'sentiment' in display_df.columns:
    sentiment_map = {'positive': '正面', 'neutral': '中性', 'negative': '负面'}
    display_df['sentiment'] = display_df['sentiment'].map(sentiment_map)

st.dataframe(display_df, use_container_width=True, hide_index=True)

# ==================== 导出功能 ====================

col_export1, col_export2 = st.columns(2)

with col_export1:
    st.download_button(
        label="📥 导出 CSV",
        data=df.to_csv(index=False).encode('utf-8-sig'),
        file_name=f"舆情数据_{datetime.now().strftime('%Y%m%d')}.csv",
        mime='text/csv',
        use_container_width=True
    )

with col_export2:
    try:
        import io
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='舆情数据')
        
        excel_data = output.getvalue()
        
        st.download_button(
            label="📊 导出 Excel",
            data=excel_data,
            file_name=f"舆情数据_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            use_container_width=True
        )
    except ImportError:
        st.info("安装 openpyxl 后支持 Excel 导出")

# ==================== 页脚 ====================

st.markdown("---")
st.caption("🚀 Powered by Streamlit Cloud + Supabase | 舆情监控系统")
