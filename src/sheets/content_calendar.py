# Google Sheet 内容日历管理模块

import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict
import gspread
from oauth2client.service_account import ServiceAccountCredentials

logger = logging.getLogger(__name__)


class ContentCalendar:
    """Google Sheet 内容日历管理"""
    
    def __init__(self, credentials_path: str = None, sheet_key: str = None):
        """
        初始化 Google Sheet 连接
        
        Args:
            credentials_path: credentials.json 文件路径
            sheet_key: Google Sheet 的 key（从 URL 获取）
        """
        self.credentials_path = credentials_path or os.environ.get("GOOGLE_CREDENTIALS_PATH")
        self.sheet_key = sheet_key or os.environ.get("CONTENT_CALENDAR_SHEET_KEY")
        self.client = None
        self.sheet = None
        
        if self.credentials_path and self.sheet_key:
            self._connect()
    
    def _connect(self):
        """连接 Google Sheets"""
        try:
            scope = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive",
            ]
            creds = ServiceAccountCredentials.from_json_keyfile_name(
                self.credentials_path, scope
            )
            self.client = gspread.authorize(creds)
            self.sheet = self.client.open_by_key(self.sheet_key).sheet1
            logger.info("  ✅  Google Sheet 连接成功")
        except Exception as e:
            logger.error(f"  ❌  Google Sheet 连接失败: {e}")
    
    def add_content(
        self,
        date: str,
        platform: str,
        account: str,
        persona: str,
        content: str,
        media_url: str = "",
        status: str = "pending",
    ) -> bool:
        """
        添加内容到日历
        
        Args:
            date: 发布日期 (YYYY-MM-DD HH:MM)
            platform: 平台 (facebook, tiktok, xcom)
            account: 账号 ID
            persona: 人设 ID
            content: 文案内容
            media_url: 图片/视频 URL
            status: 状态
            
        Returns:
            成功返回 True
        """
        if not self.sheet:
            logger.warning("Google Sheet 未连接，跳过写入")
            return False
        
        try:
            row = [
                datetime.now().isoformat(),  # 创建时间
                date,                         # 发布日期
                platform,
                account,
                persona,
                content,
                media_url,
                status,
                "",                          # 发布结果
                "",                          # 备注
            ]
            self.sheet.append_row(row)
            logger.info(f"  ✅  已添加内容: {platform}/{account} @ {date}")
            return True
        except Exception as e:
            logger.error(f"  ❌  添加内容失败: {e}")
            return False
    
    def get_pending_content(self, limit: int = 10) -> List[Dict]:
        """获取待发布内容"""
        if not self.sheet:
            return []
        
        try:
            records = self.sheet.get_all_records()
            pending = [r for r in records if r.get("status") == "pending"]
            return pending[:limit]
        except Exception as e:
            logger.error(f"  ❌  获取待发布内容失败: {e}")
            return []
    
    def update_status(self, row_index: int, status: str, result: str = ""):
        """更新状态"""
        if not self.sheet:
            return
        
        try:
            # status 列是第 8 列（H）
            self.sheet.update_cell(row_index, 8, status)
            if result:
                # result 列是第 9 列（I）
                self.sheet.update_cell(row_index, 9, result)
        except Exception as e:
            logger.error(f"  ❌  更新状态失败: {e}")


def create_content_calendar_template():
    """创建内容日历模板的说明"""
    template = """
# Google Sheet 内容日历模板

创建一个新的 Google Sheet，包含以下列：

| 列 | 名称 | 说明 |
|----|------|------|
| A | created_at | 创建时间 |
| B | publish_date | 发布日期 |
| C | platform | 平台 |
| D | account | 账号 ID |
| E | persona | 人设 |
| F | content | 文案 |
| G | media_url | 图片/视频 URL |
| H | status | 状态 |
| I | result | 发布结果 |
| J | notes | 备注 |

状态值：
- pending: 待发布
- published: 已发布
- failed: 发布失败

步骤：
1. 创建 Google Sheet
2. 第一行填写列名
3. 分享给 Service Account 邮箱（编辑权限）
4. 从 URL 复制 sheet_key
5. 设置环境变量 CONTENT_CALENDAR_SHEET_KEY
"""
    return template


if __name__ == "__main__":
    print(create_content_calendar_template())
