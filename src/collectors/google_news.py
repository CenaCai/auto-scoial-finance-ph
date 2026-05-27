# 新闻采集模块 — Google News RSS + Serper PAA

import feedparser
import logging
from datetime import datetime, timedelta
from typing import List, Dict
import requests

logger = logging.getLogger(__name__)


class NewsCollector:
    """菲律宾金融新闻采集器"""
    
    def __init__(self):
        self.rss_base = "https://news.google.com/rss/search"
    
    def fetch_google_news(self, query: str, max_items: int = 10) -> List[Dict]:
        """
        从 Google News RSS 抓取新闻
        
        Args:
            query: 搜索关键词
            max_items: 最大返回条数
            
        Returns:
            [{"title", "url", "summary", "published", "source"}, ...]
        """
        url = f"{self.rss_base}?q={query}&hl=en-PH&gl=PH&ceid=PH:en"
        
        try:
            feed = feedparser.parse(url)
            items = []
            
            for entry in feed.entries[:max_items]:
                # 解析发布时间
                published = datetime(*entry.published_parsed[:6]) if hasattr(entry, 'published_parsed') else None
                
                items.append({
                    "title": entry.get("title", ""),
                    "url": entry.get("link", ""),
                    "summary": entry.get("summary", ""),
                    "published": published.isoformat() if published else None,
                    "source": entry.get("source", {}).get("title", "Unknown"),
                    "query": query,
                })
            
            logger.info(f"  📰  Google News '{query}': {len(items)} 条")
            return items
            
        except Exception as e:
            logger.error(f"  ❌  Google News 抓取失败: {e}")
            return []
    
    def fetch_all_queries(self, queries: List[str], max_per_query: int = 5) -> List[Dict]:
        """批量抓取多个关键词的新闻"""
        all_news = []
        
        for query in queries:
            news = self.fetch_google_news(query, max_per_query)
            all_news.extend(news)
        
        # 去重（按 URL）
        seen_urls = set()
        unique_news = []
        for item in all_news:
            if item["url"] not in seen_urls:
                seen_urls.add(item["url"])
                unique_news.append(item)
        
        logger.info(f"  ✅  总计: {len(unique_news)} 条去重后新闻")
        return unique_news
    
    def fetch_serper_paa(self, question: str, serper_api_key: str) -> List[str]:
        """
        使用 Serper API 挖掘 PAA (People Also Ask) 问题
        
        Returns:
            ["question1", "question2", ...]
        """
        url = "https://google.serper.dev/search"
        headers = {"X-API-KEY": serper_api_key}
        params = {"q": question, "gl": "ph", "hl": "en"}
        
        try:
            resp = requests.post(url, headers=headers, json=params, timeout=15)
            data = resp.json()
            
            paa_questions = []
            for item in data.get("peopleAlsoAsk", []):
                q = item.get("question", "")
                if q:
                    paa_questions.append(q)
            
            return paa_questions
            
        except Exception as e:
            logger.error(f"  ❌  Serper PAA 失败: {e}")
            return []


if __name__ == "__main__":
    # 测试
    collector = NewsCollector()
    queries = [
        "Philippines loan",
        "Philippines microfinance",
        "BSP lending regulations",
    ]
    news = collector.fetch_all_queries(queries, max_per_query=3)
    
    for i, item in enumerate(news, 1):
        print(f"\n{i}. {item['title'][:60]}...")
        print(f"   Source: {item['source']}")
        print(f"   URL: {item['url'][:60]}...")
