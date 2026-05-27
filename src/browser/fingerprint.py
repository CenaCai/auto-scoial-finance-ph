# 指纹浏览器自动化模块 — 多账号管理

import os
import logging
import json
import time
from pathlib import Path
from typing import Dict, Optional, Tuple
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

logger = logging.getLogger(__name__)


class FingerprintBrowser:
    """
    指纹浏览器管理
    
    特点：
    - 每个账号独立的浏览器配置文件
    - 固定 IP 代理
    - Cookie 持久化
    - 设备指纹固定
    """
    
    def __init__(self, account_id: str, config: Dict):
        """
        Args:
            account_id: 账号 ID
            config: 配置字典，包含 proxy, user_agent, viewport 等
        """
        self.account_id = account_id
        self.config = config
        self.cookie_dir = Path(f"data/cookies/{account_id}")
        self.cookie_dir.mkdir(parents=True, exist_ok=True)
        
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
    
    def launch(self, headless: bool = False) -> Page:
        """启动浏览器"""
        playwright = sync_playwright().start()
        
        # 浏览器配置
        launch_options = {
            "headless": headless,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        }
        
        # 代理配置（从环境变量读取）
        proxy_url = self.config.get("fingerprint", {}).get("proxy", "")
        if proxy_url.startswith("${"):
            # 替换环境变量
            var_name = proxy_url.strip("${}").split("}")[0]
            proxy_url = os.environ.get(var_name, "")
        
        if proxy_url:
            launch_options["proxy"] = {"server": proxy_url}
            logger.info(f"  🌐  使用代理: {proxy_url[:20]}...")
        
        self.browser = playwright.chromium.launch(**launch_options)
        
        # 创建上下文（带指纹配置）
        context_options = {
            "user_agent": self.config.get("fingerprint", {}).get("user_agent"),
            "viewport": self.config.get("fingerprint", {}).get("viewport"),
            "locale": self.config.get("fingerprint", {}).get("locale", "en-PH"),
            "timezone_id": self.config.get("fingerprint", {}).get("timezone", "Asia/Manila"),
            "geolocation": {"latitude": 14.5995, "longitude": 120.9846},  # Manila
            "permissions": ["geolocation"],
        }
        
        self.context = self.browser.new_context(**context_options)
        
        # 加载已保存的 Cookie
        cookie_file = self.cookie_dir / "cookies.json"
        if cookie_file.exists():
            try:
                cookies = json.loads(cookie_file.read_text())
                self.context.add_cookies(cookies)
                logger.info(f"  🍪  已加载 Cookie ({len(cookies)} 个)")
            except Exception as e:
                logger.warning(f"  ⚠️  加载 Cookie 失败: {e}")
        
        self.page = self.context.new_page()
        
        logger.info(f"  ✅  浏览器已启动: {self.account_id}")
        return self.page
    
    def save_cookies(self):
        """保存 Cookie"""
        if not self.context:
            return
        
        try:
            cookies = self.context.cookies()
            cookie_file = self.cookie_dir / "cookies.json"
            cookie_file.write_text(json.dumps(cookies, indent=2))
            logger.info(f"  💾  已保存 Cookie ({len(cookies)} 个)")
        except Exception as e:
            logger.error(f"  ❌  保存 Cookie 失败: {e}")
    
    def close(self):
        """关闭浏览器"""
        if self.page:
            self.page.close()
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        
        logger.info(f"  🔒  浏览器已关闭: {self.account_id}")
    
    def __enter__(self):
        return self.launch()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.save_cookies()
        self.close()


class FacebookPublisher(FingerprintBrowser):
    """Facebook 自动发帖"""
    
    def login_check(self) -> bool:
        """检查登录状态"""
        self.page.goto("https://www.facebook.com/", timeout=30000)
        time.sleep(2)
        
        # 检查是否已登录
        current_url = self.page.url
        if "login" in current_url:
            logger.warning("  ⚠️  未登录，请手动登录")
            return False
        
        logger.info("  ✅  已登录 Facebook")
        return True
    
    def post_to_page(self, page_name: str, content: str, image_path: str = None) -> bool:
        """
        发布到 Facebook Page
        
        Args:
            page_name: Page 名称或 ID
            content: 文案
            image_path: 图片路径
            
        Returns:
            成功返回 True
        """
        try:
            # 进入 Page
            self.page.goto(f"https://www.facebook.com/{page_name}", timeout=30000)
            time.sleep(3)
            
            # 点击发帖框
            create_post = self.page.locator('[aria-label="Create post"]')
            if create_post.count() > 0:
                create_post.first.click()
            else:
                # 备用选择器
                self.page.click('div[role="button"]:has-text("Create post")')
            
            time.sleep(2)
            
            # 输入内容
            self.page.keyboard.type(content)
            time.sleep(1)
            
            # 上传图片
            if image_path:
                # 点击图片上传按钮
                self.page.click('[aria-label="Photo/Video"]')
                time.sleep(1)
                
                # 上传文件
                file_input = self.page.locator('input[type="file"]')
                file_input.set_input_files(image_path)
                time.sleep(3)
            
            # 发布
            self.page.click('[aria-label="Post"]')
            time.sleep(3)
            
            logger.info(f"  ✅  已发布到 Facebook Page: {page_name}")
            return True
            
        except Exception as e:
            logger.error(f"  ❌  发布失败: {e}")
            return False
    
    def post_to_group(self, group_id: str, content: str, image_path: str = None) -> bool:
        """发布到 Facebook Group"""
        try:
            self.page.goto(f"https://www.facebook.com/groups/{group_id}", timeout=30000)
            time.sleep(3)
            
            # 点击写帖子
            self.page.click('[aria-label="Write something..."]')
            time.sleep(2)
            
            self.page.keyboard.type(content)
            time.sleep(1)
            
            if image_path:
                self.page.click('[aria-label="Photo/Video"]')
                time.sleep(1)
                file_input = self.page.locator('input[type="file"]')
                file_input.set_input_files(image_path)
                time.sleep(3)
            
            self.page.click('[aria-label="Post"]')
            time.sleep(3)
            
            logger.info(f"  ✅  已发布到 Group: {group_id}")
            return True
            
        except Exception as e:
            logger.error(f"  ❌  发布到 Group 失败: {e}")
            return False


class TikTokPublisher(FingerprintBrowser):
    """TikTok 自动发布"""
    
    def login_check(self) -> bool:
        """检查登录状态"""
        self.page.goto("https://www.tiktok.com/", timeout=30000)
        time.sleep(3)
        
        # 检查是否有登录按钮
        login_btn = self.page.locator('button:has-text("Log in")')
        if login_btn.count() > 0:
            logger.warning("  ⚠️  TikTok 未登录")
            return False
        
        logger.info("  ✅  已登录 TikTok")
        return True
    
    def upload_video(self, video_path: str, caption: str, hashtags: list = None) -> bool:
        """
        上传 TikTok 视频
        
        Args:
            video_path: 视频文件路径
            caption: 视频描述
            hashtags: 话题标签列表
            
        Returns:
            成功返回 True
        """
        try:
            self.page.goto("https://www.tiktok.com/upload", timeout=30000)
            time.sleep(3)
            
            # 上传视频
            file_input = self.page.locator('input[type="file"]')
            file_input.set_input_files(video_path)
            time.sleep(5)  # 等待上传
            
            # 输入描述
            if hashtags:
                caption += " " + " ".join(f"#{t}" for t in hashtags)
            
            caption_box = self.page.locator('[data-testid="caption-textarea"]')
            caption_box.fill(caption)
            time.sleep(1)
            
            # 发布
            self.page.click('button:has-text("Post")')
            time.sleep(3)
            
            logger.info("  ✅  TikTok 视频已上传")
            return True
            
        except Exception as e:
            logger.error(f"  ❌  TikTok 上传失败: {e}")
            return False


class XComPublisher(FingerprintBrowser):
    """X.com (Twitter) 自动发推"""
    
    def login_check(self) -> bool:
        """检查登录状态"""
        self.page.goto("https://x.com/", timeout=30000)
        time.sleep(3)
        
        # 检查是否有登录按钮
        login_btn = self.page.locator('a[href="/login"]')
        if login_btn.count() > 0:
            logger.warning("  ⚠️  X.com 未登录")
            return False
        
        logger.info("  ✅  已登录 X.com")
        return True
    
    def post_tweet(self, content: str, image_path: str = None) -> bool:
        """
        发布推文
        
        Args:
            content: 推文内容（最多 280 字符）
            image_path: 图片路径
            
        Returns:
            成功返回 True
        """
        try:
            # 确保长度限制
            content = content[:280]
            
            # 点击发推按钮
            self.page.goto("https://x.com/compose/post", timeout=30000)
            time.sleep(2)
            
            # 输入内容
            tweet_box = self.page.locator('[data-testid="tweetTextarea_0"]')
            tweet_box.fill(content)
            time.sleep(1)
            
            # 上传图片
            if image_path:
                file_input = self.page.locator('input[type="file"]')
                file_input.set_input_files(image_path)
                time.sleep(3)
            
            # 发布
            self.page.click('[data-testid="tweetButtonInline"]')
            time.sleep(3)
            
            logger.info("  ✅  推文已发布")
            return True
            
        except Exception as e:
            logger.error(f"  ❌  发布推文失败: {e}")
            return False


if __name__ == "__main__":
    # 测试
    import yaml
    
    with open("config/accounts.yaml") as f:
        accounts = yaml.safe_load(f)["accounts"]
    
    account = accounts[0]
    
    fb = FacebookPublisher(account["id"], account)
    with fb:
        if fb.login_check():
            fb.post_to_page("YourPageName", "Test post from automation!")
