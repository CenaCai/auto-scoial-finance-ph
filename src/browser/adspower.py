# AdsPower 集成模块 — 指纹浏览器管理

import os
import logging
import requests
import time
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class AdsPowerClient:
    """
    AdsPower API 客户端
    
    AdsPower 是一款指纹浏览器管理平台，支持：
    - 多账号独立浏览器配置
    - 固定 IP 代理
    - Cookie 持久化
    - 自动化脚本
    
    API 文档：https://local.adspower.net/
    """
    
    def __init__(self):
        self.base_url = os.environ.get("ADSPOWER_API_URL", "http://local.adspower.net:50325")
        self.api_key = os.environ.get("ADSPOWER_API_KEY", "")
        
    def _request(self, endpoint: str, method: str = "GET", params: Dict = None) -> Dict:
        """发送 API 请求"""
        url = f"{self.base_url}{endpoint}"
        headers = {}
        
        if self.api_key:
            params = params or {}
            params["api_key"] = self.api_key
        
        try:
            if method == "GET":
                resp = requests.get(url, params=params, timeout=30)
            else:
                resp = requests.post(url, json=params, timeout=30)
            
            data = resp.json()
            if data.get("code") == 0:
                return data.get("data", {})
            else:
                logger.error(f"AdsPower API 错误: {data.get('msg', 'Unknown')}")
                return {}
                
        except Exception as e:
            logger.error(f"AdsPower API 请求失败: {e}")
            return {}
    
    def list_browsers(self, group_id: str = None) -> List[Dict]:
        """
        获取浏览器配置列表
        
        Args:
            group_id: 分组 ID（可选）
            
        Returns:
            [{"user_id", "name", "group", "proxy", ...}, ...]
        """
        params = {}
        if group_id:
            params["group_id"] = group_id
            
        data = self._request("/api/v1/user/list", params=params)
        return data.get("list", [])
    
    def get_browser_status(self, user_id: str) -> Dict:
        """
        检查浏览器是否已启动
        
        Returns:
            {"status": 0/1, "websocket": "..."}
        """
        return self._request("/api/v1/browser/active", params={"user_id": user_id})
    
    def start_browser(self, user_id: str, headless: bool = False) -> Dict:
        """
        启动浏览器
        
        Args:
            user_id: AdsPower 浏览器配置 ID
            headless: 是否无头模式
            
        Returns:
            {"ws", "http"} — Playwright/Selenium 连接信息
        """
        params = {
            "user_id": user_id,
            "launch_args": [],
        }
        
        if headless:
            params["launch_args"].append("--headless")
        
        data = self._request("/api/v1/browser/start", params=params)
        
        if data:
            logger.info(f"  ✅  浏览器已启动: {user_id}")
            return {
                "ws_endpoint": data.get("ws", {}).get("puppeteer"),
                "debugger_url": data.get("ws", {}).get("selenium"),
            }
        else:
            logger.error(f"  ❌  启动浏览器失败: {user_id}")
            return {}
    
    def stop_browser(self, user_id: str) -> bool:
        """关闭浏览器"""
        data = self._request("/api/v1/browser/stop", params={"user_id": user_id})
        return bool(data)
    
    def create_browser(self, name: str, proxy: Dict = None, group_id: str = None) -> str:
        """
        创建新的浏览器配置
        
        Args:
            name: 配置名称
            proxy: 代理配置 {"host", "port", "user", "pass"}
            group_id: 分组 ID
            
        Returns:
            user_id
        """
        config = {
            "name": name,
            "group_id": group_id or "0",
            "user_proxy_config": {
                "proxy_soft": "other",
                "proxy_type": "http",
            },
        }
        
        if proxy:
            config["user_proxy_config"].update({
                "host": proxy.get("host", ""),
                "port": proxy.get("port", "8080"),
                "proxy_user": proxy.get("user", ""),
                "proxy_password": proxy.get("pass", ""),
            })
        
        data = self._request("/api/v1/user/create", method="POST", params=config)
        user_id = data.get("id", "")
        
        if user_id:
            logger.info(f"  ✅  创建浏览器配置: {name} → {user_id}")
        
        return user_id


class AdsPowerPublisher:
    """
    基于 AdsPower 的社媒自动发布
    
    工作流程：
    1. 通过 AdsPower API 启动指定账号的浏览器
    2. 获取 WebSocket 连接，用 Playwright 控制
    3. 执行登录/发帖操作
    4. 关闭浏览器（Cookie 自动保存）
    """
    
    def __init__(self):
        self.client = AdsPowerClient()
    
    def publish_facebook(self, user_id: str, content: str, image_path: str = None) -> bool:
        """
        通过 AdsPower 发布 Facebook
        
        Args:
            user_id: AdsPower 浏览器配置 ID
            content: 文案
            image_path: 图片路径
            
        Returns:
            成功返回 True
        """
        from playwright.sync_api import sync_playwright
        
        # 1. 启动浏览器
        conn_info = self.client.start_browser(user_id)
        if not conn_info:
            return False
        
        ws_endpoint = conn_info.get("ws_endpoint", "")
        
        try:
            # 2. 连接 Playwright
            playwright = sync_playwright().start()
            browser = playwright.chromium.connect_over_cdp(ws_endpoint)
            
            # 获取已打开的页面
            contexts = browser.contexts
            if contexts:
                page = contexts[0].pages[0] if contexts[0].pages else contexts[0].new_page()
            else:
                page = browser.new_page()
            
            # 3. 执行发帖
            page.goto("https://www.facebook.com/", timeout=30000)
            time.sleep(3)
            
            # 检查是否已登录
            if "login" in page.url:
                logger.warning("  ⚠️  未登录，请先在 AdsPower 中手动登录")
                return False
            
            # 点击发帖框
            page.click('[aria-label="Create post"]')
            time.sleep(2)
            
            # 输入内容
            page.keyboard.type(content)
            time.sleep(1)
            
            # 上传图片
            if image_path:
                page.click('[aria-label="Photo/Video"]')
                time.sleep(1)
                file_input = page.locator('input[type="file"]')
                file_input.set_input_files(image_path)
                time.sleep(3)
            
            # 发布
            page.click('[aria-label="Post"]')
            time.sleep(3)
            
            logger.info(f"  ✅  Facebook 发布成功")
            return True
            
        except Exception as e:
            logger.error(f"  ❌  发布失败: {e}")
            return False
            
        finally:
            # 4. 关闭浏览器（Cookie 自动保存）
            self.client.stop_browser(user_id)
    
    def publish_tiktok(self, user_id: str, video_path: str, caption: str) -> bool:
        """
        通过 AdsPower 发布 TikTok
        
        Args:
            user_id: AdsPower 浏览器配置 ID
            video_path: 视频路径
            caption: 视频描述
            
        Returns:
            成功返回 True
        """
        from playwright.sync_api import sync_playwright
        
        conn_info = self.client.start_browser(user_id)
        if not conn_info:
            return False
        
        ws_endpoint = conn_info.get("ws_endpoint", "")
        
        try:
            playwright = sync_playwright().start()
            browser = playwright.chromium.connect_over_cdp(ws_endpoint)
            
            contexts = browser.contexts
            page = contexts[0].pages[0] if contexts and contexts[0].pages else browser.new_page()
            
            # 进入 TikTok 上传页
            page.goto("https://www.tiktok.com/upload", timeout=30000)
            time.sleep(3)
            
            # 检查登录状态
            if "login" in page.url.lower():
                logger.warning("  ⚠️  未登录 TikTok")
                return False
            
            # 上传视频
            file_input = page.locator('input[type="file"]')
            file_input.set_input_files(video_path)
            time.sleep(5)
            
            # 输入描述
            caption_box = page.locator('[data-testid="caption-textarea"]')
            caption_box.fill(caption)
            time.sleep(1)
            
            # 发布
            page.click('button:has-text("Post")')
            time.sleep(3)
            
            logger.info(f"  ✅  TikTok 发布成功")
            return True
            
        except Exception as e:
            logger.error(f"  ❌  TikTok 发布失败: {e}")
            return False
            
        finally:
            self.client.stop_browser(user_id)


if __name__ == "__main__":
    # 测试 AdsPower 连接
    client = AdsPowerClient()
    browsers = client.list_browsers()
    
    print(f"\n找到 {len(browsers)} 个浏览器配置:")
    for b in browsers[:5]:
        print(f"  - {b.get('user_id')}: {b.get('name')}")
