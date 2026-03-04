#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
百度 NLP 情感分析 - 样本测试（3条）
"""

import json
import os
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

import requests


class BaiduNLP:
    """百度 NLP 客户端"""
    
    def __init__(self):
        self.api_key = os.getenv("BAIDU_NLP_API_KEY")
        self.secret_key = os.getenv("BAIDU_NLP_SECRET_KEY")
        self.access_token = None
        
        if not self.api_key or not self.secret_key:
            raise ValueError("请配置 BAIDU_NLP_API_KEY 和 BAIDU_NLP_SECRET_KEY")
    
    def get_token(self):
        """获取 access_token"""
        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.secret_key
        }
        resp = requests.post(url, params=params, timeout=10)
        result = resp.json()
        if "access_token" not in result:
            raise Exception(f"获取token失败: {result}")
        self.access_token = result["access_token"]
        print("[OK] 获取 access_token 成功\n")
        return self.access_token
    
    def analyze(self, text: str) -> dict:
        """情感分析"""
        url = "https://aip.baidubce.com/rpc/2.0/nlp/v1/sentiment_classify"
        params = {"access_token": self.access_token}
        
        # 限制长度
        text = text[:2048]
        
        resp = requests.post(
            url, 
            params=params, 
            json={"text": text},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        result = resp.json()
        
        if "error_code" in result:
            raise Exception(f"API错误: {result}")
        
        item = result["items"][0]
        sentiment_map = {0: "negative", 1: "neutral", 2: "positive"}
        
        return {
            "sentiment": sentiment_map[item["sentiment"]],
            "confidence": round(item["confidence"], 3),
            "positive_prob": round(item["positive_prob"], 3),
            "negative_prob": round(item["negative_prob"], 3)
        }


def clean_text(title: str, desc: str) -> str:
    """清理文本，去除话题标签"""
    import re
    # 合并标题和描述
    text = f"{title}\n{desc}".strip()
    # 清理话题标签 #xxx[话题]#
    text = re.sub(r'#.*?\[话题\]#', '', text)
    # 清理剩余 #
    text = re.sub(r'#', '', text)
    # 清理 [表情] 如 [失望R]
    text = re.sub(r'\[\w+\]', '', text)
    return text.strip()


def load_sample_data(file_path: str, n: int = 3) -> list:
    """加载前n条样本"""
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data[:n]


def main():
    # 样本数据文件
    data_file = Path(__file__).parent.parent / "data" / "xhs" / "json" / "search_contents_2026-03-03.json"
    
    if not data_file.exists():
        print(f"[FAIL] 文件不存在: {data_file}")
        sys.exit(1)
    
    # 加载3条样本
    samples = load_sample_data(data_file, n=3)
    print(f"[INFO] 加载 {len(samples)} 条样本数据\n")
    
    # 初始化百度NLP
    try:
        nlp = BaiduNLP()
        nlp.get_token()
    except Exception as e:
        print(f"[FAIL] 初始化失败: {e}")
        sys.exit(1)
    
    # 测试3条样本
    print("=" * 60)
    print("开始情感分析测试")
    print("=" * 60)
    
    icons = {"positive": "😊", "neutral": "😐", "negative": "😔"}
    
    for i, note in enumerate(samples, 1):
        title = note.get("title", "")
        desc = note.get("desc", "")
        text = clean_text(title, desc)
        
        print(f"\n【样本 {i}】")
        print(f"标题: {title[:60]}{'...' if len(title) > 60 else ''}")
        print(f"清理后文本: {text[:100]}{'...' if len(text) > 100 else ''}")
        
        try:
            result = nlp.analyze(text)
            icon = icons.get(result["sentiment"], "❓")
            
            print(f"结果: {icon} {result['sentiment'].upper()}")
            print(f"  置信度: {result['confidence']}")
            print(f"  正向概率: {result['positive_prob']}")
            print(f"  负向概率: {result['negative_prob']}")
            
        except Exception as e:
            print(f"[FAIL] 分析失败: {e}")
        
        # QPS限制，间隔0.6秒
        if i < len(samples):
            time.sleep(0.6)
    
    print("\n" + "=" * 60)
    print("[DONE] 样本测试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
