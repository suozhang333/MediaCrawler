# -*- coding: utf-8 -*-
"""
Supabase 客户端封装 (REST API版本，无需supabase-py)
"""
import os
import requests
from typing import List, Dict, Optional


class SupabaseClient:
    """Supabase REST API 客户端"""
    
    def __init__(self, url: str = None, key: str = None):
        self.url = url or os.getenv("SUPABASE_URL")
        self.key = key or os.getenv("SUPABASE_KEY")
        
        if not self.url or not self.key:
            raise ValueError("请配置 SUPABASE_URL 和 SUPABASE_KEY")
        
        # 确保URL以/结尾
        self.url = self.url.rstrip("/")
        self.table_name = "xhs_notes"
        
        self.headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }
    
    def upsert_notes(self, notes: List[Dict]) -> Dict:
        """
        批量插入或更新笔记 (UPSERT)
        
        Args:
            notes: 笔记列表
            
        Returns:
            {"success": int, "failed": int, "errors": List}
        """
        result = {"success": 0, "failed": 0, "errors": []}
        
        for note in notes:
            try:
                # 清理数据
                clean_note = self._clean_note(note)
                
                # UPSERT: on_conflict=note_id
                resp = requests.post(
                    f"{self.url}/rest/v1/{self.table_name}",
                    headers={**self.headers, "Prefer": "resolution=merge-duplicates"},
                    json=clean_note,
                    timeout=10
                )
                
                if resp.status_code in [200, 201, 204]:
                    result["success"] += 1
                else:
                    result["failed"] += 1
                    result["errors"].append({
                        "note_id": note.get("note_id"),
                        "status": resp.status_code,
                        "error": resp.text[:200]
                    })
                    
            except Exception as e:
                result["failed"] += 1
                result["errors"].append({
                    "note_id": note.get("note_id"),
                    "error": str(e)
                })
        
        return result
    
    def _clean_note(self, note: Dict) -> Dict:
        """清理笔记数据，只保留需要的字段"""
        return {
            "note_id": note.get("note_id"),
            "title": note.get("title", ""),
            "desc": note.get("desc", ""),
            "nickname": note.get("nickname", ""),
            "liked_count": self._parse_int(note.get("liked_count")),
            "comment_count": self._parse_int(note.get("comment_count")),
            "ip_location": note.get("ip_location", ""),
            "note_url": note.get("note_url", ""),
            "source_keyword": note.get("source_keyword", ""),
            "sentiment": note.get("sentiment"),
            "publish_time": self._parse_timestamp(note.get("time")),
        }
    
    @staticmethod
    def _parse_int(value) -> int:
        """解析整数"""
        if not value:
            return 0
        try:
            return int(value)
        except (ValueError, TypeError):
            return 0
    
    @staticmethod
    def _parse_timestamp(value) -> Optional[str]:
        """解析时间戳为ISO格式"""
        if not value:
            return None
        try:
            from datetime import datetime
            # 小红书时间戳是毫秒
            ts = int(value)
            if ts > 1e12:  # 毫秒转秒
                ts = ts / 1000
            return datetime.fromtimestamp(ts).isoformat()
        except (ValueError, TypeError):
            return None
    
    def check_connection(self) -> bool:
        """检查连接是否正常"""
        try:
            resp = requests.get(
                f"{self.url}/rest/v1/{self.table_name}?select=count&limit=1",
                headers=self.headers,
                timeout=5
            )
            return resp.status_code in [200, 401]  # 401表示表存在但可能需要权限
        except Exception as e:
            print(f"[Supabase] 连接检查失败: {e}")
            return False
    
    def query_notes(self, limit: int = 100, order_by: str = "last_modify_ts", 
                    order_desc: bool = True, sentiment: str = None) -> List[Dict]:
        """
        查询笔记数据
        
        Args:
            limit: 返回数量限制
            order_by: 排序字段
            order_desc: 是否倒序
            sentiment: 筛选情感倾向 (positive/neutral/negative)
            
        Returns:
            笔记列表
        """
        try:
            params = {
                "select": "*",
                "order": f"{order_by}.{'desc' if order_desc else 'asc'}",
                "limit": limit
            }
            
            if sentiment:
                params["sentiment"] = f"eq.{sentiment}"
            
            resp = requests.get(
                f"{self.url}/rest/v1/{self.table_name}",
                headers=self.headers,
                params=params,
                timeout=10
            )
            
            if resp.status_code == 200:
                return resp.json()
            else:
                print(f"[Supabase] 查询失败: {resp.status_code} - {resp.text}")
                return []
                
        except Exception as e:
            print(f"[Supabase] 查询异常: {e}")
            return []
    
    def get_sentiment_stats(self) -> Dict:
        """获取情感分析统计"""
        try:
            # 查询各情感类型的数量
            resp = requests.get(
                f"{self.url}/rest/v1/{self.table_name}",
                headers=self.headers,
                params={"select": "sentiment"},
                timeout=10
            )
            
            if resp.status_code == 200:
                data = resp.json()
                from collections import Counter
                sentiments = [note.get('sentiment', 'unknown') for note in data]
                return dict(Counter(sentiments))
            else:
                return {}
                
        except Exception as e:
            print(f"[Supabase] 统计异常: {e}")
            return {}
