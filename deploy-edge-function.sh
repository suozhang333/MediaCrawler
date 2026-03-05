#!/bin/bash
# 部署 Supabase Edge Function

echo "🚀 部署情感分析 Edge Function..."

# 设置环境变量（从 .env 读取）
export $(grep -v '^#' .env | xargs)

# 部署函数
supabase functions deploy sentiment \
  --project-ref sblkxpeyrxbhvsehgyxf \
  --no-verify-jwt

# 设置环境变量
echo "🔧 设置环境变量..."
supabase secrets set --project-ref sblkxpeyrxbhvsehgyxf \
  BAIDU_NLP_API_KEY="$BAIDU_NLP_API_KEY" \
  BAIDU_NLP_SECRET_KEY="$BAIDU_NLP_SECRET_KEY"

echo "✅ 部署完成！"
echo ""
echo "函数地址: https://sblkxpeyrxbhvsehgyxf.supabase.co/functions/v1/sentiment"
