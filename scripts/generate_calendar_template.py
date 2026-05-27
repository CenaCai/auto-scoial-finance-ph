#!/usr/bin/env python3
"""
生成 Google Sheet 内容日历模板
输出为 CSV 格式，可手动导入到 Sheet
"""

import csv
from datetime import datetime, timedelta

# 表头
HEADERS = [
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

# 示例内容
SAMPLES = [
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

#PinoyLife #Budgeting #SweldoTips""",
        "media_url": "",
        "media_local": "data/media/tiktok_emergency.png",
        "news_source": "",
        "news_title": "",
        "priority": "high",
        "status": "pending",
        "result": "",
        "posted_at": "",
        "notes": "手动添加口播和音乐",
    },
    {
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "publish_date": (datetime.now() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M"),
        "platform": "xcom",
        "account_id": "educator_x",
        "persona": "finance_educator",
        "content": """💡 5 Things Banks Don't Tell You About Personal Loans

1. Your credit score affects your rate
2. Pre-approval ≠ guaranteed approval
3. Early payment may have fees
4. Insurance is often optional
5. You can negotiate terms

Be smart. Compare at creditkaagapay.com

#Finance101 #PHFinance #LoanPH""",
        "media_url": "",
        "media_local": "data/media/xcom_5tips.png",
        "news_source": "",
        "news_title": "",
        "priority": "normal",
        "status": "pending",
        "result": "",
        "posted_at": "",
        "notes": "",
    },
    {
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "publish_date": (datetime.now() + timedelta(hours=12)).strftime("%Y-%m-%d %H:%M"),
        "platform": "facebook",
        "account_id": "advisor_fb",
        "persona": "professional_advisor",
        "content": """⚠️ Warning Signs of Predatory Lending

Avoid lenders who:
• Ask for upfront fees
• Don't provide clear terms
• Pressure you to decide immediately
• Use intimidation tactics

Protect yourself. Research at creditkaagapay.com

#FinancePH #LoanSafety #CreditKaagapay""",
        "media_url": "",
        "media_local": "data/media/predatory_loan.png",
        "news_source": "https://news.abs-cbn.com/",
        "news_title": "New loan scam warning in Manila",
        "priority": "high",
        "status": "pending",
        "result": "",
        "posted_at": "",
        "notes": "贷款相关，优先发布",
    },
    {
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "publish_date": (datetime.now() + timedelta(hours=15)).strftime("%Y-%m-%d %H:%M"),
        "platform": "tiktok",
        "account_id": "worker_tiktok",
        "persona": "relatable_worker",
        "content": """Share ko lang guys, before akong nag-apply ng loan, I made sure to check muna sa CreditKaagapay. Ayoko ma-scam! 🙅‍♀️

Legit naman sila, helpful for comparing rates. Try nyo din!

#Budgeting #LoanPH #PinoyTips""",
        "media_url": "",
        "media_local": "data/media/tiktok_review.png",
        "news_source": "",
        "news_title": "",
        "priority": "normal",
        "status": "pending",
        "result": "",
        "posted_at": "",
        "notes": "手动添加口播和音乐",
    },
]


def generate_csv(filename="content_calendar_template.csv"):
    """生成 CSV 模板"""
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=HEADERS)
        writer.writeheader()
        for row in SAMPLES:
            writer.writerow(row)
    
    print(f"✅ 已生成: {filename}")
    print(f"   共 {len(SAMPLES)} 条示例内容")


def generate_instructions():
    """生成导入说明"""
    instructions = """
╔══════════════════════════════════════════════════════════════════╗
║          Google Sheet 内容日历导入说明                          ║
╚══════════════════════════════════════════════════════════════════╝

📁 生成的文件: content_calendar_template.csv

📥 导入到 Google Sheet:

1. 打开你的 Google Sheet:
   https://docs.google.com/spreadsheets/d/1CDBJm4DemWRK8-ud5SWhN80Co7Dfa3D2OGxKF7hkmXw/edit

2. 点击 "文件" → "导入" → "上传"

3. 上传 content_calendar_template.csv

4. 选择导入选项:
   - 导入位置: 从当前工作表的第 1 行开始
   - 分隔符: 逗号
   - 编码: UTF-8

5. 点击 "导入数据"

✅ 导入后检查:
   - 第 1 行是表头（15 列）
   - 第 2-6 行是示例内容
   - 状态列默认为 "pending"

📊 列说明:

| 列 | 名称 | 用途 |
|----|------|------|
| A  | created_at | 内容创建时间 |
| B  | publish_date | 计划发布时间 |
| C  | platform | 平台 |
| D  | account_id | 账号 ID |
| E  | persona | 人设 |
| F  | content | 完整文案 |
| G  | media_url | 图片/视频 URL |
| H  | media_local | 本地媒体路径 |
| I  | news_source | 新闻来源 URL |
| J  | news_title | 新闻标题 |
| K  | priority | 优先级 |
| L  | status | 状态 |
| M  | result | 发布结果 |
| N  | posted_at | 实际发布时间 |
| O  | notes | 备注 |

🎯 状态值:
   - pending: 待发布
   - processing: 发布中
   - published: 已发布
   - failed: 发布失败
   - skipped: 已跳过

⚠️ 优先级:
   - high: 贷款相关，必发
   - normal: 金融相关，正常发布
   - low: 其他，可选发布

"""
    return instructions


if __name__ == "__main__":
    generate_csv()
    print(generate_instructions())
