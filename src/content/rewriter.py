# 内容改写模块 — AI 改写 + 人设适配

import os
import logging
from typing import Dict, List
import requests
import yaml

logger = logging.getLogger(__name__)


class ContentRewriter:
    """AI 内容改写 + 人设适配"""
    
    def __init__(self, personas_path: str = "config/personas.yaml"):
        self.gemini_api_key = os.environ.get("GEMINI_API_KEY")
        self.personas = self._load_personas(personas_path)
    
    def _load_personas(self, path: str) -> Dict:
        """加载人设配置"""
        try:
            with open(path, "r") as f:
                return yaml.safe_load(f).get("personas", {})
        except Exception as e:
            logger.warning(f"无法加载人设配置: {e}")
            return {}
    
    def rewrite_for_platform(
        self,
        content: str,
        persona_id: str,
        platform: str,
        include_cta: bool = True,
    ) -> str:
        """
        根据平台和人设改写内容
        
        Args:
            content: 原始新闻内容
            persona_id: 人设 ID (如 "professional_advisor")
            platform: 平台 (facebook, tiktok, xcom)
            include_cta: 是否包含 CTA 引流
            
        Returns:
            改写后的文案
        """
        persona = self.personas.get(persona_id, {})
        
        # 平台限制
        limits = {
            "xcom": 280,
            "facebook": 500,
            "tiktok": 150,  # 标题/描述
        }
        
        prompt = self._build_prompt(content, persona, platform)
        
        # 调用 Gemini API
        rewritten = self._call_gemini(prompt)
        
        # 长度限制
        max_len = limits.get(platform, 500)
        if len(rewritten) > max_len:
            rewritten = rewritten[:max_len - 3] + "..."
        
        # 添加 CTA
        if include_cta and persona.get("call_to_action"):
            cta = f"\n\n{persona['call_to_action']}"
            if len(rewritten) + len(cta) <= max_len:
                rewritten += cta
        
        return rewritten
    
    def _build_prompt(self, content: str, persona: Dict, platform: str) -> str:
        """构建 AI Prompt"""
        tone = persona.get("tone", "professional")
        style = persona.get("style", "informative")
        
        platform_hints = {
            "facebook": "适合 Facebook 群组或主页，可以稍长一些",
            "tiktok": "TikTok 视频标题，简短有力，吸引眼球",
            "xcom": "Twitter/X 推文，简洁明了，带话题标签",
        }
        
        prompt = f"""你是一位菲律宾金融博主，负责撰写社交媒体内容。

风格要求：
- 语气：{tone}
- 风格：{style}
- 平台：{platform_hints.get(platform, platform)}

原始内容：
{content}

请改写为适合该平台的帖子，要求：
1. 保持原意，换表达方式
2. 符合人设风格
3. 自然融入金融知识
4. 吸引菲律宾受众

直接输出改写后的内容，不要解释。"""
        
        return prompt
    
    def _call_gemini(self, prompt: str) -> str:
        """调用 Gemini API"""
        if not self.gemini_api_key:
            logger.warning("GEMINI_API_KEY 未配置，返回原文")
            return prompt.split("\n\n原始内容：\n")[-1].split("\n\n请改写")[0]
        
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-lite:generateContent?key={self.gemini_api_key}"
            
            resp = requests.post(
                url,
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.8,
                        "maxOutputTokens": 500,
                    },
                },
                timeout=30,
            )
            
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
            
        except Exception as e:
            logger.error(f"Gemini API 调用失败: {e}")
            return prompt.split("\n\n原始内容：\n")[-1].split("\n\n请改写")[0]


if __name__ == "__main__":
    # 测试
    rewriter = ContentRewriter()
    
    test_content = """
    The Bangko Sentral ng Pilipinas (BSP) has announced new regulations 
    for digital lending platforms, requiring them to disclose all fees 
    and interest rates upfront.
    """
    
    for persona_id in ["professional_advisor", "relatable_worker"]:
        for platform in ["facebook", "tiktok", "xcom"]:
            print(f"\n=== {persona_id} @ {platform} ===")
            result = rewriter.rewrite_for_platform(test_content, persona_id, platform)
            print(result)
