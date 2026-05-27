# Google Sheet 内容日历模板生成器

"""
内容日历字段设计：

| 列 | 字段名 | 说明 | 示例 |
|----|--------|------|------|
| A | created_at | 创建时间 | 2026-05-27 17:00:00 |
| B | publish_date | 发布日期 | 2026-05-28 09:00 |
| C | platform | 平台 | facebook / tiktok / xcom |
| D | account_id | 账号 ID | advisor_fb |
| E | persona | 人设 | professional_advisor |
| F | content | 文案 | (完整文案内容) |
| G | media_url | 图片/视频 URL | https://... |
| H | media_local | 本地媒体路径 | data/media/tiktok_1.png |
| I | news_source | 新闻来源 URL | https://news... |
| J | news_title | 新闻原标题 | BSP announces... |
| K | priority | 优先级 | high / normal |
| L | status | 状态 | pending / published / failed |
| M | result | 发布结果 | Post ID: xxx |
| N | posted_at | 实际发布时间 | 2026-05-28 09:05 |
| O | notes | 备注 | 手动调整发布时间 |

状态值：
- pending: 待发布（队列中）
- processing: 发布中
- published: 已发布
- failed: 发布失败
- skipped: 已跳过

优先级：
- high: 贷款相关，必发
- normal: 金融相关，正常发布
- low: 其他，可选发布
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta


def setup_content_calendar(credentials_path: str, sheet_key: str):
    """
    设置内容日历工作表
    
    需要提前：
    1. 创建 Google Cloud 项目
    2. 启用 Google Sheets API
    3. 创建 Service Account 并下载 credentials.json
    4. 将 Service Account 邮箱添加到 Sheet 的共享列表（编辑权限）
    """
    
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    
    creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scope)
    client = gspread.authorize(creds)
    
    # 打开指定的 Sheet
    sheet = client.open_by_key(sheet_key)
    
    # 获取第一个工作表（或创建）
    try:
        worksheet = sheet.get_worksheet(0)
    except:
        worksheet = sheet.add_worksheet(title="内容日历", rows=1000, cols=15)
    
    # 设置表头
    headers = [
        "created_at",
        "publish_date", 
        "platform",
        "account_id",
        "persona",
        "content",
        "media_url",
        "media_local",
        "news_source",
        "news_title",
        "priority",
        "status",
        "result",
        "posted_at",
        "notes",
    ]
    
    # 检查是否已有表头
    first_row = worksheet.row_values(1)
    if not first_row or first_row[0] != headers[0]:
        worksheet.insert_row(headers, 1)
        print("✅ 已添加表头")
    
    # 设置列宽（建议）
    column_widths = {
        'A': 20,  # created_at
        'B': 15,  # publish_date
        'C': 12,  # platform
        'D': 15,  # account_id
        'E': 20,  # persona
        'F': 80,  # content
        'G': 40,  # media_url
        'H': 30,  # media_local
        'I': 40,  # news_source
        'J': 40,  # news_title
        'K': 10,  # priority
        'L': 12,  # status
        'M': 30,  # result
        'N': 20,  # posted_at
        'O': 30,  # notes
    }
    
    # 设置数据验证（状态）
    try:
        # 状态列只能选择特定值
        worksheet.set_data_validation(
            'L2:L1000',
            gspread.models.DataValidationRule(
                gspread.models.BooleanCondition(
                    'ONE_OF_LIST',
                    ['pending', 'processing', 'published', 'failed', 'skipped']
                ),
                showCustomUi=True
            )
        )
        
        # 优先级列
        worksheet.set_data_validation(
            'K2:K1000',
            gspread.models.DataValidationRule(
                gspread.models.BooleanCondition(
                    'ONE_OF_LIST',
                    ['high', 'normal', 'low']
                ),
                showCustomUi=True
            )
        )
        print("✅ 已设置数据验证")
    except Exception as e:
        print(f"⚠️  数据验证设置失败（可忽略）: {e}")
    
    print(f"\n📊 内容日历已配置: {sheet_key}")
    return worksheet


def add_sample_content(worksheet):
    """添加示例内容"""
    
    samples = [
        {
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "publish_date": (datetime.now() + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M"),
            "platform": "facebook",
            "account_id": "advisor_fb",
            "persona": "professional_advisor",
            "content": """📊 Understanding Loan Interest Rates in the Philippines

Before applying for a loan, understand the difference between:
• Nominal Rate — the stated rate
• Effective Rate — the actual cost including fees
• APR — Annual Percentage Rate (best for comparison)

💡 Tip: Always compare APR, not just interest rate.

Visit creditkaagapay.com to compare trusted lenders.

#FinancePH #LoanTips""",
            "media_url": "",
            "media_local": "data/media/loan_tips_1.png",
            "news_source": "https://www.bsp.gov.ph/",
            "news_title": "BSP releases new lending guidelines",
            "priority": "high",
            "status": "pending",
            "result": "",
            "posted_at": "",
            "notes": "贷款相关，优先发布",
        },
        {
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "publish_date": (datetime.now() + timedelta(hours=5)).strftime("%Y-%m-%d %H:%M"),
            "platform": "tiktok",
            "account_id": "worker_tiktok",
            "persona": "relatable_worker",
            "content": """Nakakastress talaga kapag biglaang gastos! 😅

Buti na lang may trusted loan options. Search "CreditKaagapay" para sa legit lenders! 💪

#PinoyLife #Budgeting""",
            "media_url": "",
            "media_local": "data/media/tiktok_emergency.png",
            "news_source": "",
            "news_title": "",
            "priority": "high",
            "status": "pending",
            "result": "",
            "posted_at": "",
            "notes": "TikTok 需要手动添加口播和音乐",
        },
    ]
    
    for sample in samples:
        worksheet.append_row(list(sample.values()))
    
    print(f"\n✅ 已添加 {len(samples)} 条示例内容")


if __name__ == "__main__":
    import os
    
    # 从环境变量读取配置
    creds_path = os.environ.get("GOOGLE_CREDENTIALS_PATH", "./credentials.json")
    sheet_key = os.environ.get("CONTENT_CALENDAR_SHEET_KEY", "YOUR_SHEET_KEY")
    
    # 设置内容日历
    worksheet = setup_content_calendar(creds_path, sheet_key)
    
    # 添加示例内容（可选）
    # add_sample_content(worksheet)
    
    print("\n" + "="*60)
    print("📋 Google Sheet 内容日历配置完成")
    print("="*60)
    print(f"""
下一步：
1. 确保已将 Service Account 邮箱添加到 Sheet 共享列表
2. 设置环境变量：
   - GOOGLE_CREDENTIALS_PATH=/path/to/credentials.json
   - CONTENT_CALENDAR_SHEET_KEY={sheet_key}
3. 运行 python -m src.main --mode workflow
""")
