# -*- coding: utf-8 -*-
"""
企业微信 Webhook 推送
"""
import json
import requests
from typing import Dict, List


class WechatWorkWebhook:
    """企业微信机器人 Webhook"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    def send_markdown(self, content: str) -> bool:
        """发送 Markdown 消息"""
        data = {
            "msgtype": "markdown",
            "markdown": {"content": content}
        }
        return self._send(data)
    
    def _send(self, data: Dict) -> bool:
        """发送请求"""
        try:
            resp = requests.post(self.webhook_url, json=data, timeout=10)
            result = resp.json()
            return result.get("errcode") == 0
        except Exception as e:
            print(f"[WechatWork] 发送失败: {e}")
            return False


class NegativeAlertPusher:
    """负面舆情实时推送器"""
    
    def __init__(self, webhook_url: str = None):
        self.webhook = WechatWorkWebhook(webhook_url) if webhook_url else None
        self.negative_buffer = []  # 缓冲负面笔记
    
    def add_negative(self, note: Dict):
        """添加一条负面笔记到缓冲"""
        self.negative_buffer.append({
            "note_id": note.get("note_id"),
            "title": note.get("title", "无标题")[:50],
            "desc": note.get("desc", "")[:100],
            "url": note.get("note_url", ""),
            "keyword": note.get("source_keyword", ""),
            "sentiment": note.get("sentiment"),
        })
    
    def push_if_needed(self, force: bool = False) -> bool:
        """
        推送负面舆情（如果有）
        
        Args:
            force: 强制推送，无视数量
        
        Returns:
            是否成功推送
        """
        if not self.webhook:
            return False
        
        if not self.negative_buffer:
            return True
        
        if not force and len(self.negative_buffer) < 1:
            return True
        
        # 构建 Markdown 告警
        content = self._build_alert()
        success = self.webhook.send_markdown(content)
        
        if success:
            print(f"[Alert] 负面舆情推送成功: {len(self.negative_buffer)} 条")
            self.negative_buffer.clear()
        else:
            print(f"[Alert] 负面舆情推送失败")
        
        return success
    
    def _build_alert(self) -> str:
        """构建告警消息"""
        lines = [
            "## 🚨 负面舆情告警",
            f"**检测到 {len(self.negative_buffer)} 条负面笔记**",
            "---",
        ]
        
        for i, note in enumerate(self.negative_buffer[:5], 1):
            lines.append(f"**{i}. {note['title']}**")
            lines.append(f"> 关键词：{note['keyword']}")
            lines.append(f"> 摘要：{note['desc']}...")
            lines.append(f"> [查看笔记]({note['url']})")
            lines.append("")
        
        if len(self.negative_buffer) > 5:
            lines.append(f"*还有 {len(self.negative_buffer) - 5} 条...*")
        
        lines.append("---")
        lines.append("⏰ 请及时处理")
        
        return "\n".join(lines)
