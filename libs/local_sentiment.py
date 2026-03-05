# -*- coding: utf-8 -*-
"""
本地情感分析 - 使用 SnowNLP
无需网络，适合公司内网环境
"""
from snownlp import SnowNLP
from typing import Dict


class LocalSentimentAnalyzer:
    """本地情感分析器 - 基于 SnowNLP"""
    
    def analyze(self, text: str) -> Dict:
        """
        分析文本情感
        
        Args:
            text: 待分析文本
            
        Returns:
            {
                "sentiment": "positive/neutral/negative",
                "confidence": float,
                "positive_prob": float,
                "negative_prob": float
            }
        """
        if not text or len(text.strip()) == 0:
            return {
                "sentiment": None,
                "confidence": 0,
                "positive_prob": 0,
                "negative_prob": 0
            }
        
        # SnowNLP 情感分析 (0-1, 越接近1越正面)
        s = SnowNLP(text)
        sentiment_score = s.sentiments
        
        # 转换为三分类
        if sentiment_score > 0.6:
            sentiment = "positive"
        elif sentiment_score < 0.4:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        return {
            "sentiment": sentiment,
            "confidence": abs(sentiment_score - 0.5) * 2,  # 置信度
            "positive_prob": sentiment_score,
            "negative_prob": 1 - sentiment_score
        }


def test():
    """测试"""
    analyzer = LocalSentimentAnalyzer()
    
    test_texts = [
        "这个餐厅真好吃，服务也很好！",
        "一般般，没什么特别的",
        "太差了，永远不会再来",
        "南航的飞机餐还可以"
    ]
    
    for text in test_texts:
        result = analyzer.analyze(text)
        print(f"文本: {text}")
        print(f"结果: {result}")
        print()


if __name__ == "__main__":
    test()
