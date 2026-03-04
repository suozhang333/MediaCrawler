# -*- coding: utf-8 -*-
"""
百度 NLP 情感分析客户端
"""
import os
import requests


class BaiduNLP:
    """百度 NLP 情感分析客户端"""
    
    def __init__(self, api_key: str = None, secret_key: str = None):
        self.api_key = api_key or os.getenv("BAIDU_NLP_API_KEY")
        self.secret_key = secret_key or os.getenv("BAIDU_NLP_SECRET_KEY")
        self.access_token = None
        
        if not self.api_key or not self.secret_key:
            raise ValueError("请配置 BAIDU_NLP_API_KEY 和 BAIDU_NLP_SECRET_KEY")
        
        self._get_access_token()
    
    def _get_access_token(self):
        """获取百度 API access token"""
        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.secret_key
        }
        
        response = requests.post(url, params=params)
        result = response.json()
        
        if "access_token" not in result:
            raise Exception(f"获取 token 失败: {result}")
        
        self.access_token = result["access_token"]
    
    def sentiment(self, text: str) -> dict:
        """
        情感分析
        返回: {
            "sentiment": "positive/neutral/negative",
            "confidence": float,
            "positive_prob": float,
            "negative_prob": float
        }
        """
        url = "https://aip.baidubce.com/rpc/2.0/nlp/v1/sentiment_classify"
        params = {"access_token": self.access_token}
        
        # 百度 API 限制：文本长度不超过 2048 字节
        text = text[:2048]
        
        payload = {"text": text}
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(url, params=params, json=payload, headers=headers)
        result = response.json()
        
        if "error_code" in result:
            raise Exception(f"API 错误: {result}")
        
        item = result["items"][0]
        
        # 百度返回: 0-负向, 1-中性, 2-正向
        sentiment_map = {0: "negative", 1: "neutral", 2: "positive"}
        
        return {
            "sentiment": sentiment_map[item["sentiment"]],
            "confidence": item["confidence"],
            "positive_prob": item["positive_prob"],
            "negative_prob": item["negative_prob"]
        }
    
    def analyze(self, text: str) -> dict:
        """sentiment 的别名"""
        return self.sentiment(text)
