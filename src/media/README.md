# 图片生成说明

## 方案：静态图片 + 文字叠加

**工作流程：**
1. 从 Pexels API 搜索相关金融图片（免费）
2. 使用 Pillow 叠加文字（标题 + 副标题 + 引导语）
3. 生成 1080x1920 竖版图片（TikTok 尺寸）
4. 用户在 TikTok 发布时手动添加：
   - 口播（使用 TikTok 自带功能）
   - 背景音乐（TikTok 音乐库）

## TikTok 发布流程

### 方式 1：通过 AdsPower 自动上传图片
```
1. AdsPower API 启动浏览器
2. 进入 TikTok 上传页：https://www.tiktok.com/upload
3. 上传生成的图片
4. 填写标题（文案）
5. 点击发布
6. 手动打开 TikTok App 添加口播和音乐（推荐）
```

### 方式 2：直接上传视频
```
1. 使用手机拍摄口播视频
2. 或使用 CapCut 生成文字动画视频
3. 通过 AdsPower 上传
```

## 图片模板示例

```python
TIKTOK_TEMPLATES = [
    {
        "title": "5 Loan Tips\nfor Filipinos",
        "subtitle": "Search CreditKaagapay\nfor trusted lenders",
        "bg_query": "money",  # Pexels 搜索关键词
    },
    {
        "title": "Avoid These\n3 Loan Mistakes",
        "subtitle": "Learn more at\nCreditKaagapay.com",
        "bg_query": "calculator",
    },
]
```

## 配置

在 `.env` 中设置：
```
PEXELS_API_KEY=your_pexels_api_key
```

申请 Pexels API：https://www.pexels.com/api/

## 注意事项

1. **口播建议手动添加** — TikTok 自带的口播功能效果最好
2. **音乐选择热门曲目** — 增加曝光度
3. **图片文字简洁** — TikTok 用户快速滑过，信息要一目了然
4. **引导搜索而非链接** — 避免被判定为广告降权
