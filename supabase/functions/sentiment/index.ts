// Supabase Edge Function: 情感分析服务
// 调用百度 NLP API，绕过本地网络限制

import { serve } from "https://deno.land/std@0.168.0/http/server.ts";

const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

// 百度 NLP 配置（从环境变量读取）
const BAIDU_API_KEY = Deno.env.get("BAIDU_NLP_API_KEY") || "";
const BAIDU_SECRET_KEY = Deno.env.get("BAIDU_NLP_SECRET_KEY") || "";

serve(async (req) => {
  // 处理 CORS
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: CORS_HEADERS });
  }

  try {
    const { text } = await req.json();
    
    if (!text) {
      return new Response(
        JSON.stringify({ error: "Missing text parameter" }),
        { status: 400, headers: { ...CORS_HEADERS, "Content-Type": "application/json" } }
      );
    }

    // 获取百度 access_token
    const tokenUrl = `https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=${BAIDU_API_KEY}&client_secret=${BAIDU_SECRET_KEY}`;
    
    const tokenResp = await fetch(tokenUrl, { method: "POST" });
    const tokenData = await tokenResp.json();
    
    if (!tokenData.access_token) {
      return new Response(
        JSON.stringify({ error: "Failed to get Baidu token", detail: tokenData }),
        { status: 500, headers: { ...CORS_HEADERS, "Content-Type": "application/json" } }
      );
    }

    // 调用百度情感分析 API
    const sentimentUrl = `https://aip.baidubce.com/rpc/2.0/nlp/v1/sentiment_classify?access_token=${tokenData.access_token}`;
    
    const sentimentResp = await fetch(sentimentUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: text.slice(0, 2048) }), // 百度限制 2048 字节
    });
    
    const sentimentData = await sentimentResp.json();
    
    if (sentimentData.error_code) {
      return new Response(
        JSON.stringify({ error: "Baidu API error", detail: sentimentData }),
        { status: 500, headers: { ...CORS_HEADERS, "Content-Type": "application/json" } }
      );
    }

    // 解析结果
    const item = sentimentData.items[0];
    const sentimentMap: { [key: number]: string } = { 0: "negative", 1: "neutral", 2: "positive" };
    
    const result = {
      sentiment: sentimentMap[item.sentiment],
      confidence: item.confidence,
      positive_prob: item.positive_prob,
      negative_prob: item.negative_prob,
      provider: "baidu",
    };

    return new Response(
      JSON.stringify(result),
      { headers: { ...CORS_HEADERS, "Content-Type": "application/json" } }
    );

  } catch (error) {
    return new Response(
      JSON.stringify({ error: error.message }),
      { status: 500, headers: { ...CORS_HEADERS, "Content-Type": "application/json" } }
    );
  }
});
