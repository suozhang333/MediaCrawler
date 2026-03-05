# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler/blob/main/main.py
# GitHub: https://github.com/NanmiCoder
# Licensed under NON-COMMERCIAL LEARNING LICENSE 1.1
#

# 声明：本代码仅供学习和研究目的使用。使用者应遵守以下原则：
# 1. 不得用于任何商业用途。
# 2. 使用时应遵守目标平台的使用条款和robots.txt规则。
# 3. 不得进行大规模爬取或对平台造成运营干扰。
# 4. 应合理控制请求频率，避免给目标平台带来不必要的负担。
# 5. 不得用于任何非法或不当的用途。
#
# 详细许可条款请参阅项目根目录下的LICENSE文件。
# 使用本代码即表示您同意遵守上述原则和LICENSE中的所有条款。

import sys
import io

# Force UTF-8 encoding for stdout/stderr to prevent encoding errors
# when outputting Chinese characters in non-UTF-8 terminals
if sys.stdout and hasattr(sys.stdout, 'buffer'):
    if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'buffer'):
    if sys.stderr.encoding and sys.stderr.encoding.lower() != 'utf-8':
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import asyncio
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Type

# Load environment variables
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

# Setup logging
os.makedirs("logs", exist_ok=True)
log_file = f"logs/crawler_{datetime.now().strftime('%Y%m%d')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

import cmd_arg
import config
from database import db
from base.base_crawler import AbstractCrawler
from media_platform.bilibili import BilibiliCrawler
from media_platform.douyin import DouYinCrawler
from media_platform.kuaishou import KuaishouCrawler
from media_platform.tieba import TieBaCrawler
from media_platform.weibo import WeiboCrawler
from media_platform.xhs import XiaoHongShuCrawler
from media_platform.zhihu import ZhihuCrawler
from tools.async_file_writer import AsyncFileWriter
from var import crawler_type_var


class CrawlerFactory:
    CRAWLERS: dict[str, Type[AbstractCrawler]] = {
        "xhs": XiaoHongShuCrawler,
        "dy": DouYinCrawler,
        "ks": KuaishouCrawler,
        "bili": BilibiliCrawler,
        "wb": WeiboCrawler,
        "tieba": TieBaCrawler,
        "zhihu": ZhihuCrawler,
    }

    @staticmethod
    def create_crawler(platform: str) -> AbstractCrawler:
        crawler_class = CrawlerFactory.CRAWLERS.get(platform)
        if not crawler_class:
            supported = ", ".join(sorted(CrawlerFactory.CRAWLERS))
            raise ValueError(f"Invalid media platform: {platform!r}. Supported: {supported}")
        return crawler_class()


crawler: Optional[AbstractCrawler] = None


def _flush_excel_if_needed() -> None:
    if config.SAVE_DATA_OPTION != "excel":
        return

    try:
        from store.excel_store_base import ExcelStoreBase

        ExcelStoreBase.flush_all()
        print("[Main] Excel files saved successfully")
    except Exception as e:
        print(f"[Main] Error flushing Excel data: {e}")


async def _generate_wordcloud_if_needed() -> None:
    if config.SAVE_DATA_OPTION != "json" or not config.ENABLE_GET_WORDCLOUD:
        return

    try:
        file_writer = AsyncFileWriter(
            platform=config.PLATFORM,
            crawler_type=crawler_type_var.get(),
        )
        await file_writer.generate_wordcloud_from_comments()
    except Exception as e:
        print(f"[Main] Error generating wordcloud: {e}")


async def _run_sentiment_analysis_if_needed() -> None:
    """Run sentiment analysis and save to Supabase if enabled"""
    if not config.ENABLE_SENTIMENT_ANALYSIS:
        return
    
    if config.SAVE_DATA_OPTION != "json":
        print("[Main] Sentiment analysis only supports JSON mode currently")
        return
    
    try:
        from libs.sentiment_processor import SentimentProcessor, find_latest_json
        
        # 查找最新JSON文件
        data_dir = Path(__file__).parent / "data" / config.PLATFORM / "json"
        data_file = find_latest_json(data_dir)
        
        if not data_file:
            print("[Main] No JSON data file found for sentiment analysis")
            return
        
        print(f"\n[Main] Starting sentiment analysis: {data_file.name}")
        
        # 执行情感分析
        processor = SentimentProcessor()
        result = processor.run(data_file)
        
        # 结果显示在 processor.run() 内部已打印，这里只打印简洁总结
        print(f"[Main] ✓ 情感分析完成: {result['saved']}/{result['total']} 条已存入 Supabase")
            
    except Exception as e:
        print(f"[Main] Error running sentiment analysis: {e}")


async def run_crawler_once():
    """执行一次完整的爬取流程"""
    global crawler
    
    crawler = CrawlerFactory.create_crawler(platform=config.PLATFORM)
    await crawler.start()

    _flush_excel_if_needed()
    await _generate_wordcloud_if_needed()
    await _run_sentiment_analysis_if_needed()


async def run_scheduler(interval_minutes: int):
    """定时任务模式：循环执行爬取"""
    import time
    
    logger.info(f"{'='*60}")
    logger.info("🚀 定时任务模式启动")
    logger.info(f"   平台: {config.PLATFORM}")
    logger.info(f"   关键词: {config.KEYWORDS}")
    logger.info(f"   间隔: {interval_minutes} 分钟")
    logger.info(f"{'='*60}")
    
    # 同时输出到控制台
    print(f"\n{'='*60}")
    print("🚀 定时任务模式启动")
    print(f"   平台: {config.PLATFORM}")
    print(f"   关键词: {config.KEYWORDS}")
    print(f"   间隔: {interval_minutes} 分钟")
    print(f"{'='*60}\n")
    
    # 首次立即执行
    logger.info("首次执行")
    print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 首次执行")
    await run_crawler_once()
    logger.info("首次执行完成")
    print(f"✅ 首次执行完成\n")
    
    # 循环定时执行
    while True:
        logger.info(f"等待 {interval_minutes} 分钟后下次执行...")
        print(f"⏳ 等待 {interval_minutes} 分钟后下次执行...")
        time.sleep(interval_minutes * 60)
        
        logger.info("定时执行")
        print(f"\n🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 定时执行")
        await run_crawler_once()
        logger.info("执行完成")
        print(f"✅ 执行完成\n")


async def main() -> None:
    global crawler

    args = await cmd_arg.parse_cmd()
    if args.init_db:
        await db.init_db(args.init_db)
        print(f"Database {args.init_db} initialized successfully.")
        return
    
    # 定时任务模式
    if config.ENABLE_SCHEDULER:
        try:
            await run_scheduler(config.SCHEDULER_INTERVAL_MINUTES)
        except KeyboardInterrupt:
            print("\n\n👋 定时任务已停止")
        return

    # 单次执行模式
    await run_crawler_once()


async def async_cleanup() -> None:
    global crawler
    if crawler:
        if getattr(crawler, "cdp_manager", None):
            try:
                await crawler.cdp_manager.cleanup(force=True)
            except Exception as e:
                error_msg = str(e).lower()
                if "closed" not in error_msg and "disconnected" not in error_msg:
                    print(f"[Main] Error cleaning up CDP browser: {e}")

        elif getattr(crawler, "browser_context", None):
            try:
                await crawler.browser_context.close()
            except Exception as e:
                error_msg = str(e).lower()
                if "closed" not in error_msg and "disconnected" not in error_msg:
                    print(f"[Main] Error closing browser context: {e}")

    if config.SAVE_DATA_OPTION in ("db", "sqlite"):
        await db.close()

if __name__ == "__main__":
    from tools.app_runner import run

    def _force_stop() -> None:
        c = crawler
        if not c:
            return
        cdp_manager = getattr(c, "cdp_manager", None)
        launcher = getattr(cdp_manager, "launcher", None)
        if not launcher:
            return
        try:
            launcher.cleanup()
        except Exception:
            pass

    run(main, async_cleanup, cleanup_timeout_seconds=15.0, on_first_interrupt=_force_stop)
