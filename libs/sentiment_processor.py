# -*- coding: utf-8 -*-
"""
情感分析处理器 - 单文件完整实现
流程: 加载JSON → 情感分析 → 存入Supabase
"""
import json
import logging
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# 添加项目根目录到路径（支持直接运行）
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv(project_root / ".env")

from libs.baidu_nlp import BaiduNLP
from libs.local_sentiment import LocalSentimentAnalyzer
from libs.supabase_client import SupabaseClient
from libs.wechat_work_webhook import NegativeAlertPusher
import os

# Setup logging
os.makedirs("logs", exist_ok=True)
log_file = f"logs/sentiment_{datetime.now().strftime('%Y%m%d')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SentimentProcessor:
    """
    情感分析处理器
    
    使用示例:
        processor = SentimentProcessor()
        result = processor.run(Path("data/xhs/json/search_contents_2026-03-04.json"))
        print(f"分析完成: {result['processed']}/{result['total']}")
    """
    
    def __init__(self, qps: float = 1.6, enable_alert: bool = True, use_local: bool = None):
        """
        初始化处理器
        
        Args:
            qps: 每秒请求数，控制百度API调用频率
            enable_alert: 是否启用负面舆情实时推送
            use_local: 是否使用本地SnowNLP（None=自动检测）
        """
        # 自动选择：公司网络用本地，其他用百度
        if use_local is None:
            use_local = os.getenv("USE_LOCAL_SENTIMENT", "false").lower() == "true"
        
        if use_local:
            logger.info("[SentimentProcessor] 使用本地 SnowNLP 情感分析")
            print("[SentimentProcessor] 使用本地 SnowNLP 情感分析")
            self.nlp = LocalSentimentAnalyzer()
            self.delay = 0.1  # 本地分析快，间隔短
        else:
            logger.info("[SentimentProcessor] 使用百度 NLP 情感分析")
            print("[SentimentProcessor] 使用百度 NLP 情感分析")
            self.nlp = BaiduNLP()
            self.delay = 1.0 / qps  # 百度API需要控制QPS
        
        self.supabase = SupabaseClient()
        self.processed = 0
        self.failed = 0
        self.negative_count = 0
        
        # 初始化负面舆情推送器
        webhook_url = os.getenv("WECHAT_WORK_WEBHOOK")
        self.alert_pusher = NegativeAlertPusher(webhook_url) if (enable_alert and webhook_url) else None
    
    def run(self, json_file: Path) -> Dict:
        """
        执行完整情感分析流程
        
        Args:
            json_file: JSON数据文件路径
            
        Returns:
            {
                "total": 总数据条数,
                "processed": 成功分析条数,
                "failed": 分析失败条数,
                "saved": 成功存储条数
            }
        """
        logger.info("=" * 60)
        logger.info("情感分析处理器启动")
        logger.info("=" * 60)
        print("=" * 60)
        print("情感分析处理器启动")
        print("=" * 60)
        
        # 1. 加载数据
        notes = self._load(json_file)
        logger.info(f"[Processor] 加载数据: {json_file.name}, 共 {len(notes)} 条")
        print(f"[Processor] 加载数据: {json_file.name}, 共 {len(notes)} 条")
        
        # 2. 情感分析
        analyzed = self._analyze_batch(notes)
        logger.info(f"[Processor] 分析完成: 成功 {self.processed}, 失败 {self.failed}")
        print(f"[Processor] 分析完成: 成功 {self.processed}, 失败 {self.failed}")
        
        # 3. 推送负面舆情告警（优先推送，及时通知）
        if self.alert_pusher and self.negative_count > 0:
            logger.warning(f"[Processor] 发现 {self.negative_count} 条负面舆情，准备推送...")
            print(f"[Processor] 发现 {self.negative_count} 条负面舆情，准备推送...")
            self.alert_pusher.push_if_needed(force=True)
        
        # 4. 存储结果到 Supabase
        result = self._save(analyzed, json_file)
        
        # 打印详细统计
        stats_msg = f"""📊 情感分析统计
  加载数据:     {len(notes):>3} 条
  分析成功:     {self.processed:>3} 条
  负面舆情:     {self.negative_count:>3} 条 {'🚨' if self.negative_count > 0 else ''}
  分析失败:     {self.failed:>3} 条
  存入Supabase: {result['success']:>3} 条"""
        logger.info(stats_msg)
        print("\n" + "=" * 60)
        print("📊 情感分析统计")
        print("=" * 60)
        print(f"  加载数据:     {len(notes):>3} 条")
        print(f"  分析成功:     {self.processed:>3} 条")
        print(f"  负面舆情:     {self.negative_count:>3} 条 {'🚨' if self.negative_count > 0 else ''}")
        print(f"  分析失败:     {self.failed:>3} 条")
        print(f"  存入Supabase: {result['success']:>3} 条")
        if result['failed'] > 0:
            logger.warning(f"  存储失败:     {result['failed']:>3} 条")
            print(f"  存储失败:     {result['failed']:>3} 条")
        print("=" * 60)
        
        return {
            "total": len(notes),
            "processed": self.processed,
            "failed": self.failed,
            "saved": result['success']
        }
    
    def _load(self, file_path: Path) -> List[Dict]:
        """加载JSON数据文件"""
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def _analyze_batch(self, notes: List[Dict]) -> List[Dict]:
        """
        批量分析笔记情感
        
        Args:
            notes: 笔记列表
            
        Returns:
            添加sentiment字段的笔记列表
        """
        results = []
        total = len(notes)
        
        for i, note in enumerate(notes, 1):
            # 清理文本
            text = self._clean_text(
                note.get("title", ""),
                note.get("desc", "")
            )
            
            # 情感分析
            if text:
                try:
                    # 百度API限制2048字节
                    result = self.nlp.analyze(text[:2048])
                    note["sentiment"] = result["sentiment"]
                    self.processed += 1
                    
                    # 实时检测负面舆情
                    if result["sentiment"] == "negative":
                        self.negative_count += 1
                        if self.alert_pusher:
                            self.alert_pusher.add_negative(note)
                            alert_msg = f"  [ALERT] 发现负面舆情: {note.get('title', '')[:30]}..."
                            logger.warning(alert_msg)
                            print(alert_msg)
                
                except Exception as e:
                    err_msg = f"  [WARN] 分析失败 {note.get('note_id')}: {e}"
                    logger.warning(err_msg)
                    print(err_msg)
                    note["sentiment"] = None
                    self.failed += 1
            else:
                note["sentiment"] = None
            
            results.append(note)
            
            # 打印进度
            if i % 5 == 0 or i == total:
                sentiment = note.get("sentiment")
                progress_msg = f"  [{i}/{total}] {sentiment or 'NULL'}"
                logger.info(progress_msg)
                print(progress_msg)
            
            # QPS控制
            if i < total:
                time.sleep(self.delay)
        
        return results
    
    def _clean_text(self, title: str, desc: str) -> str:
        """
        清理文本，去除话题标签和表情
        
        Args:
            title: 标题
            desc: 描述
            
        Returns:
            清理后的文本
        """
        text = f"{title}\n{desc}".strip()
        # 清理话题标签 #xxx[话题]#
        text = re.sub(r'#.*?\[话题\]#', '', text)
        # 清理单个#
        text = re.sub(r'#', '', text)
        # 清理表情 [xxx]
        text = re.sub(r'\[\w+\]', '', text)
        return text.strip()
    
    def _save(self, notes: List[Dict], json_file: Path = None) -> Dict:
        """
        保存到Supabase，分析后自动删除源JSON文件
        
        Args:
            notes: 分析后的笔记列表
            json_file: 源JSON文件路径
            
        Returns:
            {"success": int, "failed": int, "errors": List}
        """
        result = self.supabase.upsert_notes(notes)
        
        # 分析完成后删除源JSON文件
        if json_file and json_file.exists():
            try:
                json_file.unlink()
                logger.info(f"[Processor] 已删除源文件: {json_file.name}")
                print(f"[Processor] 已删除源文件: {json_file.name}")
            except Exception as e:
                err_msg = f"[WARN] 删除文件失败: {e}"
                logger.warning(err_msg)
                print(err_msg)
        
        return result


def find_latest_json(data_dir: Path) -> Optional[Path]:
    """
    查找最新的JSON数据文件
    
    Args:
        data_dir: 数据目录
        
    Returns:
        最新的JSON文件路径，如果没有则返回None
    """
    json_files = list(data_dir.glob("search_contents_*.json"))
    if not json_files:
        return None
    return max(json_files, key=lambda p: p.stat().st_mtime)


def load_json_data(file_path: str) -> List[Dict]:
    """加载JSON数据"""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    """命令行入口"""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description="情感分析处理器")
    parser.add_argument("--auto", action="store_true", help="自动查找最新JSON文件")
    parser.add_argument("--file", type=str, help="指定JSON文件路径")
    args = parser.parse_args()
    
    # 确定数据文件
    if args.file:
        data_file = Path(args.file)
    elif args.auto:
        data_dir = Path(__file__).parent.parent / "data" / "xhs" / "json"
        data_file = find_latest_json(data_dir)
        if not data_file:
            logger.error(f"[ERROR] 在 {data_dir} 未找到JSON文件")
            print(f"[ERROR] 在 {data_dir} 未找到JSON文件")
            sys.exit(1)
        logger.info(f"[INFO] 自动找到最新文件: {data_file.name}")
        print(f"[INFO] 自动找到最新文件: {data_file.name}")
    else:
        # 默认文件
        data_file = Path(__file__).parent.parent / "data" / "xhs" / "json" / "search_contents_2026-03-04.json"
    
    if not data_file.exists():
        logger.error(f"[ERROR] 数据文件不存在: {data_file}")
        print(f"[ERROR] 数据文件不存在: {data_file}")
        print("请先执行爬虫获取数据: python main.py --platform xhs")
        sys.exit(1)
    
    # 执行处理
    processor = SentimentProcessor()
    result = processor.run(data_file)
    
    # 返回码供主程序判断
    sys.exit(0 if result['failed'] == 0 else 1)


if __name__ == "__main__":
    main()
