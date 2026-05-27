# auto-social-finance-ph 社交媒体矩阵分发系统

## 项目定位
菲律宾金融/贷款领域的社交媒体矩阵自动化运营系统，多账号、多平台分发，引流到 creditkaagapay.com。

## 核心架构

```
┌─────────────────────────────────────────────────────────────┐
│                    News Collector (新闻采集)                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Google News │  │  Serper API │  │ Twitter/X   │         │
│  │ Philippines │  │  PAA Mining │  │ Finance PH  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   Content Pipeline (内容管道)                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ News Filter │→ │ AI Rewrite  │→ │ Media Gen   │         │
│  │ 贷款优先    │  │ 人设适配    │  │ 图片/视频    │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                Google Sheet (内容日历/文案库)                 │
│  Date | Platform | Account | Persona | Content | Media | Status │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              Browser Automation (指纹浏览器分发)             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Account #1  │  │ Account #2  │  │ Account #N  │         │
│  │ FB + TikTok │  │ FB + X.com  │  │ TikTok + X  │         │
│  │ 固定IP #1   │  │ 固定IP #2   │  │ 固定IP #N   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

## 模块拆分

### 1. 新闻采集模块 (`src/collectors/`)
- **Google News RSS** — 监控 `Philippines + finance`、`Philippines + loan`、`Philippines + lending`
- **Serper API** — PAA 问题挖掘（已有）
- **Twitter/X API** — 关注菲律宾金融博主，抓取热点话题
- **本地新闻源** — Inquirer.net、Philippine Star、GMA News

**过滤规则：**
- 贷款/借贷相关 → 必发，高优先级
- 金融理财 → 正常优先级
- 经济政策 → 正常优先级

### 2. 内容改写模块 (`src/content/`)
- **AI 改写** — 保持原意，换表达方式
- **人设适配** — 不同账号不同口吻
  - 账号A：专业理财顾问（正式、权威）
  - 账号B：打工族/用户（亲切、真实）
  - 账号C：金融科普博主（教育性）

### 3. 素材生成模块 (`src/media/`)
**图片：**
- Canva API — 批量生成图文卡片（模板化）
- Pexels/Unsplash — 配图搜索

**视频（口播）：**
- HeyGen/D-ID — AI 数字人口播视频（付费）
- Runway Gen-3 — AI 视频生成
- 或：文字转语音 + 字幕视频（剪映风格）

### 4. 指纹浏览器自动化 (`src/browser/`)
- **工具：** Playwright + 多浏览器配置
- **指纹管理：**
  - 每个 `.env` 文件对应一个账号
  - 固定 IP（通过代理）
  - 固定设备指纹（User-Agent、屏幕分辨率、WebGL 等）
- **Cookie 持久化：** GitHub Actions Cache

### 5. Google Sheet 管理 (`src/sheets/`)
- 内容日历：每天发什么、发到哪、用什么文案
- 账号管理：账号列表、人设、IP 配置
- 效果追踪：发帖后的数据（点赞、评论、分享）

### 6. 发布调度模块 (`src/scheduler/`)
- GitHub Actions Cron — 每天 3-4 个时段自动发布
- 发布前检查：文案长度、图片尺寸、敏感词过滤
- 发布后验证：检查是否成功、截图留存

## 目录结构

```
auto-social-finance-ph/
├── src/
│   ├── __init__.py
│   ├── main.py                 # 主入口
│   │
│   ├── collectors/             # 新闻采集
│   │   ├── __init__.py
│   │   ├── google_news.py      # Google News RSS
│   │   └── serper_paa.py       # Serper PAA
│   │
│   ├── content/                # 内容处理
│   │   ├── __init__.py
│   │   ├── rewriter.py         # AI 改写（Gemini）
│   │   └── filter.py           # 敏感词过滤
│   │
│   ├── media/                  # 素材生成
│   │   ├── __init__.py
│   │   ├── image_gen.py        # 图片生成（Pexels + Pillow）
│   │   └── README.md           # 图片生成说明
│   │
│   ├── browser/                # 浏览器自动化
│   │   ├── __init__.py
│   │   ├── adspower.py          # AdsPower 集成（主力）
│   │   ├── fingerprint.py       # 原生 Playwright（备选）
│   │   ├── facebook.py          # Facebook 发布逻辑
│   │   ├── tiktok.py            # TikTok 发布逻辑
│   │   └── xcom.py              # X.com 发布逻辑
│   │
│   ├── sheets/                 # Google Sheet 管理
│   │   ├── __init__.py
│   │   ├── content_calendar.py  # 内容日历读写
│   │   └── setup_calendar.py    # 初始化日历
│   │
│   └── scheduler/              # 调度发布
│       ├── __init__.py
│       └── publisher.py        # 发布调度逻辑
│
├── config/
│   ├── accounts.yaml           # 账号配置（AdsPower ID、平台）
│   ├── personas.yaml           # 人设定义
│   └── keywords.yaml           # 关键词配置
│
├── .github/workflows/
│   ├── collect-news.yml        # 每天采集新闻
│   ├── generate-content.yml    # 生成内容
│   └── publish-social.yml      # 发布社媒
│
├── data/
│   ├── cookies/                # Cookie 存储（如不用 AdsPower）
│   ├── media/                  # 生成的图片/视频
│   └── logs/                   # 运行日志
│
├── requirements.txt
├── .env.example
└── README.md
```

## 技术栈

| 模块 | 工具 | 费用 |
|------|------|------|
| 新闻采集 | Google News RSS + Serper API | 免费额度 |
| AI 改写 | Gemini 2.0 Flash | 免费额度 |
| 图片生成 | Pexels API + Pillow | 免费 |
| 视频方案 | 静态图片 + 文字（平台口播/音乐） | 免费 |
| 浏览器自动化 | AdsPower API | 免费（本地） |
| 内容管理 | Google Sheets API | 免费 |

## 发布策略

### Facebook
- **Group 发帖** — 菲律宾贷款/金融相关群组
- **Page 发帖** — 自己的公共主页
- **评论引流** — 在热门帖子下自然评论

### TikTok
- **视频发布** — 口播视频 + 字幕
- **标题优化** — #PhilippinesFinance #LoanTips #CreditKaagapay
- **引导搜索** — "搜索 CreditKaagapay 了解更多"

### X.com (Twitter)
- **推文发布** — 短文案 + 图片
- **话题参与** — 回复热门金融帖子
- **话题标签** — #PHFinance #LoanPH

## 下一步行动

1. **确认账号数量和平台分配** — 多少个 FB/TikTok/X 账号？
2. **确认代理 IP 方案** — 用哪家代理服务商？每个账号固定 IP？
3. **视频生成方案** — 用 AI 口播（付费）还是文字+字幕（免费）？
4. **Google Sheet 模板** — 我来设计内容日历模板

请确认以上问题，我开始写代码。
