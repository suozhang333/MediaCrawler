#!/bin/bash
# 启动 Streamlit 仪表盘

cd "$(dirname "$0")"

echo "🚀 启动舆情监控仪表盘..."
echo ""

# 检查依赖
pip install -r requirements.txt -q

# 启动 Streamlit
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
