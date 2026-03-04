#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Webhook 推送测试

测试企业微信、钉钉等推送功能
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv(project_root / ".env")

import requests
from datetime import datetime


def test_wechat_work():
    """测试企业微信推送"""
    import os
    
    webhook = os.getenv("WECHAT_WORK_WEBHOOK")
    
    print("=" * 60)
    print("🧪 测试企业微信 Webhook")
    print("=" * 60)
    
    if not webhook:
        print("❌ WECHAT_WORK_WEBHOOK 未配置")
        return False
    
    print(f"✅ Webhook 已配置: {webhook[:60]}...")
    
    data = {
        "msgtype": "text",
        "text": {
            "content": f"🎉 测试消息：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        }
    }
    
    try:
        resp = requests.post(webhook, json=data, timeout=10)
        result = resp.json()
        
        print(f"状态码: {resp.status_code}")
        print(f"返回: {resp.text}")
        
        if result.get("errcode") == 0:
            print("✅ 推送成功！请检查微信是否收到消息")
            return True
        else:
            print(f"❌ 推送失败: {result.get('errmsg')}")
            return False
            
    except Exception as e:
        print(f"❌ 异常: {e}")
        return False


def test_dingtalk():
    """测试钉钉推送"""
    import os
    
    webhook = os.getenv("DINGTALK_WEBHOOK")
    
    print("\n" + "=" * 60)
    print("🧪 测试钉钉 Webhook")
    print("=" * 60)
    
    if not webhook:
        print("❌ DINGTALK_WEBHOOK 未配置")
        return False
    
    print(f"✅ Webhook 已配置: {webhook[:60]}...")
    
    data = {
        "msgtype": "text",
        "text": {
            "content": f"🎉 测试消息：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        }
    }
    
    try:
        resp = requests.post(webhook, json=data, timeout=10)
        result = resp.json()
        
        print(f"状态码: {resp.status_code}")
        print(f"返回: {resp.text}")
        
        if result.get("errcode") == 0:
            print("✅ 推送成功！请检查钉钉是否收到消息")
            return True
        else:
            print(f"❌ 推送失败: {result.get('errmsg')}")
            return False
            
    except Exception as e:
        print(f"❌ 异常: {e}")
        return False


def test_negative_alert():
    """测试负面舆情推送"""
    print("\n" + "=" * 60)
    print("🧪 测试负面舆情推送")
    print("=" * 60)
    
    from libs.wechat_work_webhook import NegativeAlertPusher
    import os
    
    webhook = os.getenv("WECHAT_WORK_WEBHOOK")
    
    if not webhook:
        print("❌ WECHAT_WORK_WEBHOOK 未配置，跳过测试")
        return False
    
    pusher = NegativeAlertPusher(webhook)
    
    # 模拟负面笔记
    test_notes = [
        {
            "note_id": "test001",
            "title": "测试负面标题：产品体验很差",
            "desc": "这是一个测试的负面舆情内容，用于验证推送功能",
            "note_url": "https://xiaohongshu.com/test",
            "source_keyword": "测试关键词",
            "sentiment": "negative"
        }
    ]
    
    for note in test_notes:
        pusher.add_negative(note)
    
    print(f"✅ 添加了 {len(test_notes)} 条测试负面笔记")
    
    success = pusher.push_if_needed(force=True)
    
    if success:
        print("✅ 负面舆情推送成功！请检查微信")
        return True
    else:
        print("❌ 负面舆情推送失败")
        return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🚀 Webhook 测试套件")
    print("=" * 60 + "\n")
    
    # 运行所有测试
    results = []
    
    results.append(("企业微信", test_wechat_work()))
    results.append(("钉钉", test_dingtalk()))
    results.append(("负面舆情", test_negative_alert()))
    
    # 汇总
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    
    for name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {name}: {status}")
    
    passed = sum(1 for _, s in results if s)
    total = len(results)
    
    print(f"\n总计: {passed}/{total} 通过")
    print("=" * 60)
