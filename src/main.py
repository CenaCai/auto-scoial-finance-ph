# 主入口 — 社交媒体矩阵分发

import argparse
import logging
import yaml
from datetime import datetime, timedelta
from typing import List, Dict
import os
import sys

# 模块导入
from .collectors.google_news import NewsCollector
from .content.rewriter import ContentRewriter
from .sheets.content_calendar import ContentCalendar
from .browser.fingerprint import FacebookPublisher, TikTokPublisher, XComPublisher

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("social_matrix")


class SocialMatrixPublisher:
    """社媒矩阵分发主控"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        self.accounts = self._load_yaml("accounts.yaml")["accounts"]
        self.personas = self._load_yaml("personas.yaml")["personas"]
        self.keywords = self._load_yaml("keywords.yaml")
        
        self.news_collector = NewsCollector()
        self.content_rewriter = ContentRewriter(f"{config_dir}/personas.yaml")
        self.calendar = ContentCalendar()
    
    def _load_yaml(self, filename: str) -> Dict:
        """加载 YAML 配置"""
        path = os.path.join(self.config_dir, filename)
        try:
            with open(path, "r") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.warning(f"无法加载 {path}: {e}")
            return {}
    
    def collect_news(self, max_per_query: int = 5) -> List[Dict]:
        """采集菲律宾金融新闻"""
        queries = self.keywords.get("news_sources", {}).get("google_news", {}).get("queries", [])
        
        if not queries:
            # 默认关键词
            queries = [
                "Philippines loan",
                "Philippines finance lending",
                "BSP lending regulations",
                "Filipino personal finance",
            ]
        
        news = self.news_collector.fetch_all_queries(queries, max_per_query)
        
        # 过滤：贷款相关必发
        loan_keywords = self.keywords.get("loan_keywords", [])
        finance_keywords = self.keywords.get("finance_keywords", [])
        
        prioritized = []
        for item in news:
            title_lower = item["title"].lower()
            summary_lower = item.get("summary", "").lower()
            combined = title_lower + " " + summary_lower
            
            # 贷款关键词 → 高优先级
            if any(kw.lower() in combined for kw in loan_keywords):
                item["priority"] = "high"
                prioritized.append(item)
            # 金融关键词 → 正常优先级
            elif any(kw.lower() in combined for kw in finance_keywords):
                item["priority"] = "normal"
                prioritized.append(item)
        
        logger.info(f"  📰  采集完成: {len(prioritized)} 条（高优先级 {sum(1 for x in prioritized if x['priority']=='high')} 条）")
        return prioritized
    
    def generate_content(self, news_items: List[Dict], dry_run: bool = False) -> List[Dict]:
        """为每个账号生成内容"""
        generated = []
        
        for account in self.accounts:
            account_id = account["id"]
            persona_id = account["persona"]
            platforms = account["platforms"]
            
            persona = self.personas.get(persona_id, {})
            
            for platform in platforms:
                for news in news_items[:3]:  # 每个账号每天最多 3 条
                    content = self.content_rewriter.rewrite_for_platform(
                        news["title"] + "\n\n" + news.get("summary", ""),
                        persona_id,
                        platform.replace("_", ""),  # facebook_page → facebook
                        include_cta=True,
                    )
                    
                    if dry_run:
                        logger.info(f"\n[DRY RUN] {account_id} @ {platform}")
                        logger.info(f"  {content[:100]}...")
                    
                    generated.append({
                        "account_id": account_id,
                        "platform": platform,
                        "persona": persona_id,
                        "content": content,
                        "news_url": news["url"],
                        "news_title": news["title"],
                        "priority": news.get("priority", "normal"),
                    })
        
        logger.info(f"  ✍️  生成内容: {len(generated)} 条")
        return generated
    
    def add_to_calendar(self, generated: List[Dict]):
        """添加到 Google Sheet 内容日历"""
        for i, item in enumerate(generated):
            # 根据账号配置的发布时段分配时间
            account = next((a for a in self.accounts if a["id"] == item["account_id"]), None)
            if not account:
                continue
            
            schedule = account.get("schedule", ["09:00", "15:00", "20:00"])
            time_slot = schedule[i % len(schedule)]
            
            date_str = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d") + f" {time_slot}"
            
            self.calendar.add_content(
                date=date_str,
                platform=item["platform"],
                account=item["account_id"],
                persona=item["persona"],
                content=item["content"],
                status="pending",
            )
    
    def publish_now(self, account_id: str, platform: str, content: str, media_path: str = None) -> bool:
        """立即发布（浏览器自动化）"""
        account = next((a for a in self.accounts if a["id"] == account_id), None)
        if not account:
            logger.error(f"账号不存在: {account_id}")
            return False
        
        try:
            if platform.startswith("facebook"):
                publisher = FacebookPublisher(account_id, account)
                with publisher:
                    if not publisher.login_check():
                        logger.error("请先手动登录 Facebook")
                        return False
                    
                    if platform == "facebook_page":
                        return publisher.post_to_page("YourPageName", content, media_path)
                    elif platform == "facebook_group":
                        return publisher.post_to_group("YourGroupId", content, media_path)
            
            elif platform == "tiktok":
                publisher = TikTokPublisher(account_id, account)
                with publisher:
                    if not publisher.login_check():
                        logger.error("请先手动登录 TikTok")
                        return False
                    return publisher.upload_video(media_path, content)
            
            elif platform == "xcom":
                publisher = XComPublisher(account_id, account)
                with publisher:
                    if not publisher.login_check():
                        logger.error("请先手动登录 X.com")
                        return False
                    return publisher.post_tweet(content, media_path)
            
        except Exception as e:
            logger.error(f"发布失败: {e}")
            return False
        
        return False
    
    def run_daily_workflow(self, dry_run: bool = False):
        """每日工作流：采集 → 生成 → 入库"""
        logger.info("=" * 60)
        logger.info("  社交媒体矩阵分发 — 每日工作流")
        logger.info("=" * 60)
        
        # 1. 采集新闻
        logger.info("\n📡  采集菲律宾金融新闻...")
        news = self.collect_news(max_per_query=5)
        
        if not news:
            logger.warning("未采集到新闻，退出")
            return
        
        # 2. 生成内容
        logger.info("\n✍️  为各账号生成内容...")
        generated = self.generate_content(news, dry_run)
        
        # 3. 入库
        if not dry_run:
            logger.info("\n📋  添加到内容日历...")
            self.add_to_calendar(generated)
        
        logger.info("\n" + "=" * 60)
        logger.info("  ✅  完成！")
        logger.info("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="菲律宾金融社媒矩阵分发系统")
    parser.add_argument(
        "--mode", "-m",
        choices=["collect", "generate", "publish", "workflow"],
        default="workflow",
        help="运行模式: collect(采集) | generate(生成) | publish(发布) | workflow(完整流程)",
    )
    parser.add_argument(
        "--account", "-a",
        type=str,
        help="指定账号 ID（publish 模式）",
    )
    parser.add_argument(
        "--platform", "-p",
        type=str,
        help="指定平台（publish 模式）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="演习模式，不实际写入/发布",
    )
    parser.add_argument(
        "--config-dir",
        type=str,
        default="config",
        help="配置文件目录",
    )
    
    args = parser.parse_args()
    
    publisher = SocialMatrixPublisher(config_dir=args.config_dir)
    
    if args.mode == "workflow":
        publisher.run_daily_workflow(dry_run=args.dry_run)
    
    elif args.mode == "collect":
        news = publisher.collect_news()
        for item in news[:10]:
            print(f"\n- {item['title']}")
            print(f"  {item['url']}")
    
    elif args.mode == "generate":
        news = publisher.collect_news(max_per_query=3)
        generated = publisher.generate_content(news, dry_run=True)
    
    elif args.mode == "publish":
        if not all([args.account, args.platform]):
            logger.error("publish 模式需要 --account 和 --platform 参数")
            sys.exit(1)
        
        # 从内容日历读取待发布内容
        pending = publisher.calendar.get_pending_content(limit=1)
        if pending:
            item = pending[0]
            success = publisher.publish_now(
                args.account,
                args.platform,
                item["content"],
            )
            if success:
                logger.info("✅ 发布成功")
            else:
                logger.error("❌ 发布失败")


if __name__ == "__main__":
    main()
