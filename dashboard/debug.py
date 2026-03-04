#!/usr/bin/env python3
"""
调试页面 - 检查 Secrets 配置
"""
import streamlit as st
import os

st.title("🔍 Secrets 调试")

st.header("1. Streamlit Secrets")
try:
    st.write("SUPABASE_URL:", st.secrets.get("SUPABASE_URL", "未设置")[:50] + "...")
    st.write("SUPABASE_KEY:", "已设置" if st.secrets.get("SUPABASE_KEY") else "未设置")
except Exception as e:
    st.error(f"读取 Secrets 失败: {e}")

st.header("2. 环境变量")
st.write("SUPABASE_URL:", (os.getenv("SUPABASE_URL") or "未设置")[:50] + "...")
st.write("SUPABASE_KEY:", "已设置" if os.getenv("SUPABASE_KEY") else "未设置")

st.header("3. 测试连接")
if st.button("测试 Supabase 连接"):
    try:
        import requests
        
        # 尝试读取 Secrets
        url = st.secrets.get("SUPABASE_URL", os.getenv("SUPABASE_URL"))
        key = st.secrets.get("SUPABASE_KEY", os.getenv("SUPABASE_KEY"))
        
        if not url or not key:
            st.error("❌ 缺少配置")
        else:
            headers = {
                "apikey": key,
                "Authorization": f"Bearer {key}",
            }
            
            resp = requests.get(
                f"{url}/rest/v1/xhs_notes?select=count&limit=1",
                headers=headers,
                timeout=10
            )
            
            st.write(f"状态码: {resp.status_code}")
            st.write(f"返回: {resp.text[:200]}")
            
            if resp.status_code == 200:
                st.success("✅ 连接成功！")
            else:
                st.error(f"❌ 连接失败: {resp.status_code}")
                
    except Exception as e:
        st.error(f"❌ 异常: {e}")

st.markdown("---")
st.caption("如果 Secrets 都显示'未设置'，请检查 Streamlit Cloud 的 Secrets 配置")
