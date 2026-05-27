# TikTok 素材生成模块 — 静态图片 + 文字

import os
import logging
import requests
from PIL import Image, ImageDraw, ImageFont
from typing import List, Dict, Optional
from pathlib import Path
import textwrap

logger = logging.getLogger(__name__)


class TikTokImageGenerator:
    """
    TikTok 图片生成器
    
    生成风格：静态图片 + 文字叠加
    - 背景：金融相关图片（Pexels 免费 API）
    - 文字：关键信息 + 引导语
    - 用户自行在 TikTok 添加口播和音乐
    """
    
    def __init__(self, output_dir: str = "data/media"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.pexels_api_key = os.environ.get("PEXELS_API_KEY", "")
        
        # 字体配置（使用系统字体）
        self.font_size = 48
        self.title_font_size = 72
        
    def search_pexels_image(self, query: str, save_path: str = None) -> Optional[str]:
        """
        从 Pexels 搜索并下载图片
        
        Args:
            query: 搜索关键词（如 "money", "finance", "bank"）
            save_path: 保存路径（可选）
            
        Returns:
            图片路径，失败返回 None
        """
        if not self.pexels_api_key:
            logger.warning("PEXELS_API_KEY 未配置，使用默认背景")
            return None
        
        try:
            url = "https://api.pexels.com/v1/search"
            headers = {"Authorization": self.pexels_api_key}
            params = {
                "query": query,
                "per_page": 1,
                "orientation": "portrait",  # TikTok 竖版
            }
            
            resp = requests.get(url, headers=headers, params=params, timeout=15)
            data = resp.json()
            
            if data.get("photos"):
                photo = data["photos"][0]
                image_url = photo["src"]["large"]
                
                # 下载图片
                img_resp = requests.get(image_url, timeout=30)
                
                if not save_path:
                    save_path = self.output_dir / f"pexels_{query}_{photo['id']}.jpg"
                
                with open(save_path, "wb") as f:
                    f.write(img_resp.content)
                
                logger.info(f"  📸  下载 Pexels 图片: {save_path}")
                return str(save_path)
            
        except Exception as e:
            logger.error(f"  ❌  Pexels API 失败: {e}")
        
        return None
    
    def create_text_overlay(
        self,
        title: str,
        subtitle: str,
        background_path: str = None,
        output_path: str = None,
        width: int = 1080,
        height: int = 1920,
    ) -> str:
        """
        创建带文字的 TikTok 图片
        
        Args:
            title: 主标题（如 "5 Loan Tips"）
            subtitle: 副标题（如 "Search CreditKaagapay"）
            background_path: 背景图片路径
            output_path: 输出路径
            width: 图片宽度
            height: 图片高度
            
        Returns:
            生成的图片路径
        """
        # 1. 创建或加载背景
        if background_path and os.path.exists(background_path):
            bg = Image.open(background_path)
            bg = bg.resize((width, height), Image.Resampling.LANCZOS)
        else:
            # 使用渐变背景
            bg = Image.new("RGB", (width, height), (26, 26, 46))  # 深色背景
            draw = ImageDraw.Draw(bg)
            
            # 简单渐变效果
            for y in range(height):
                r = int(26 + (y / height) * 20)
                g = int(26 + (y / height) * 20)
                b = int(46 + (y / height) * 30)
                draw.line([(0, y), (width, y)], fill=(r, g, b))
        
        draw = ImageDraw.Draw(bg)
        
        # 2. 添加半透明遮罩（提高文字可读性）
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 100))
        bg = bg.convert("RGBA")
        bg = Image.alpha_composite(bg, overlay)
        draw = ImageDraw.Draw(bg)
        
        # 3. 绘制标题
        try:
            title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", self.title_font_size)
            subtitle_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", self.font_size)
        except:
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
        
        # 标题位置（居中，上方 1/3 处）
        title_y = height // 3
        
        # 自动换行
        wrapped_title = textwrap.fill(title, width=20)
        
        for line in wrapped_title.split("\n"):
            bbox = draw.textbbox((0, 0), line, font=title_font)
            line_width = bbox[2] - bbox[0]
            x = (width - line_width) // 2
            draw.text((x, title_y), line, font=title_font, fill=(255, 255, 255))
            title_y += self.title_font_size + 10
        
        # 4. 绘制副标题（下方）
        subtitle_y = height * 2 // 3
        wrapped_subtitle = textwrap.fill(subtitle, width=25)
        
        for line in wrapped_subtitle.split("\n"):
            bbox = draw.textbbox((0, 0), line, font=subtitle_font)
            line_width = bbox[2] - bbox[0]
            x = (width - line_width) // 2
            draw.text((x, subtitle_y), line, font=subtitle_font, fill=(255, 215, 0))  # 金色
            subtitle_y += self.font_size + 10
        
        # 5. 保存
        if not output_path:
            output_path = self.output_dir / f"tiktok_{title[:20].replace(' ', '_')}.png"
        
        bg = bg.convert("RGB")
        bg.save(output_path, "PNG", quality=95)
        
        logger.info(f"  🎨  生成 TikTok 图片: {output_path}")
        return str(output_path)
    
    def batch_generate(
        self,
        topics: List[Dict],
        pexels_queries: List[str] = None,
    ) -> List[str]:
        """
        批量生成 TikTok 图片
        
        Args:
            topics: [{"title": "...", "subtitle": "..."}, ...]
            pexels_queries: Pexels 搜索关键词列表
            
        Returns:
            生成的图片路径列表
        """
        generated = []
        queries = pexels_queries or ["finance", "money", "bank", "calculator"]
        
        for i, topic in enumerate(topics):
            # 获取背景图
            query = queries[i % len(queries)]
            bg_path = None
            
            if self.pexels_api_key:
                bg_path = self.search_pexels_image(query)
            
            # 生成图片
            output = self.create_text_overlay(
                title=topic["title"],
                subtitle=topic["subtitle"],
                background_path=bg_path,
            )
            
            generated.append(output)
        
        return generated


# 预设模板 — 菲律宾金融 TikTok 内容
TIKTOK_TEMPLATES = [
    {
        "title": "5 Loan Tips\nfor Filipinos",
        "subtitle": "Search CreditKaagapay\nfor trusted lenders",
        "pexels": "money",
    },
    {
        "title": "Avoid These\n3 Loan Mistakes",
        "subtitle": "Learn more at\nCreditKaagapay.com",
        "pexels": "calculator",
    },
    {
        "title": "Emergency Loan?\nRead This First",
        "subtitle": "Compare rates at\nCreditKaagapay",
        "pexels": "bank",
    },
    {
        "title": "OFW Loan Guide\n2026",
        "subtitle": "Find the best options\nCreditKaagapay",
        "pexels": "philippines",
    },
    {
        "title": "Your Credit Score\nMatters!",
        "subtitle": "Check your options\nCreditKaagapay.com",
        "pexels": "credit",
    },
]


if __name__ == "__main__":
    # 测试生成
    generator = TikTokImageGenerator()
    
    # 生成预设模板
    images = generator.batch_generate(TIKTOK_TEMPLATES)
    
    print(f"\n生成 {len(images)} 张 TikTok 图片:")
    for img in images:
        print(f"  - {img}")
