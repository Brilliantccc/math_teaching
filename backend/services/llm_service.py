"""LLM服务 - 支持OpenAI兼容API"""

import json
import re
import httpx
from typing import Optional, List, Dict, Any
from backend.config import settings


class LLMService:
    """LLM服务封装"""

    def __init__(self):
        self.model_id: Optional[str] = settings.LLM_MODEL_ID
        self.api_key: Optional[str] = settings.LLM_API_KEY
        self.base_url: Optional[str] = settings.LLM_BASE_URL
        self.timeout: int = settings.LLM_TIMEOUT

    def is_configured(self) -> bool:
        """检查LLM是否已配置"""
        return bool(self.api_key and self.base_url)

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def chat(self, messages: List[Dict[str, str]]) -> str:
        """发送聊天请求"""
        if not self.is_configured():
            raise ValueError("LLM未配置")

        url = f"{self.base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": self.model_id,
            "messages": messages,
            "temperature": 0.3,
        }

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(url, json=payload, headers=self._get_headers())
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    def chat_with_image(self, image_b64: str, prompt: str) -> str:
        """发送带图片的聊天请求"""
        if not self.is_configured():
            raise ValueError("LLM未配置")

        url = f"{self.base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": self.model_id,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"},
                        },
                    ],
                }
            ],
            "temperature": 0.3,
        }

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(url, json=payload, headers=self._get_headers())
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    def parse_json(self, text: str) -> Any:
        """从LLM响应中解析JSON"""
        # 清理文本
        text = text.strip()

        # 尝试直接解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # 尝试从markdown代码块中提取
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if json_match:
            try:
                return json.loads(json_match.group(1).strip())
            except json.JSONDecodeError:
                pass

        # 尝试找到第一个 [ 或 { 开始的JSON（优先数组）
        for start_char, end_char in [("[", "]"), ("{", "}")]:
            start = text.find(start_char)
            if start == -1:
                continue
            # 从后往前找匹配的结束符
            end = text.rfind(end_char)
            if end > start:
                try:
                    return json.loads(text[start : end + 1])
                except json.JSONDecodeError:
                    pass

        # 尝试逐行清理后解析
        lines = text.split('\n')
        json_lines = []
        in_json = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith(('[', '{')):
                in_json = True
            if in_json:
                json_lines.append(line)
            if in_json and stripped.endswith((']', '}')):
                try:
                    return json.loads('\n'.join(json_lines))
                except json.JSONDecodeError:
                    in_json = False
                    json_lines = []

        raise ValueError(f"无法解析JSON: {text[:300]}...")


# 全局单例
llm_service = LLMService()
