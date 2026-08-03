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

    def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: float = 0.3,
    ) -> str:
        """发送聊天请求"""
        if not self.is_configured():
            raise ValueError("LLM未配置")

        url = f"{self.base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": self.model_id,
            "messages": messages,
            "temperature": temperature,
        }

        # 添加max_tokens
        if max_tokens:
            payload["max_tokens"] = max_tokens

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(url, json=payload, headers=self._get_headers())
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    def chat_with_image(
        self,
        image_b64: str,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.3,
    ) -> str:
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
            "temperature": temperature,
        }

        # 添加max_tokens
        if max_tokens:
            payload["max_tokens"] = max_tokens

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(url, json=payload, headers=self._get_headers())
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    def parse_json(self, text: str) -> Any:
        """从LLM响应中解析JSON（带修复逻辑）"""
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

        # 尝试修复不完整的JSON
        fixed = self._try_fix_incomplete_json(text)
        if fixed is not None:
            return fixed

        raise ValueError(f"无法解析JSON: {text[:300]}...")

    def _try_fix_incomplete_json(self, text: str) -> Optional[Any]:
        """尝试修复不完整的JSON"""
        # 找到JSON数组的开始
        array_start = text.find('[')
        if array_start == -1:
            return None

        # 提取数组内容
        content = text[array_start:]

        # 尝试找到最后一个完整的对象
        # 查找最后一个 "}" 或 "]"
        last_brace = content.rfind('}')
        if last_brace == -1:
            return None

        # 尝试截断到最后一个完整对象
        truncated = content[:last_brace + 1]

        # 检查是否需要关闭数组
        if not truncated.endswith(']'):
            truncated += ']'

        try:
            return json.loads(truncated)
        except json.JSONDecodeError:
            pass

        # 尝试更激进的修复：找到最后一个逗号后的完整对象
        last_comma = truncated.rfind(',')
        if last_comma != -1:
            truncated = truncated[:last_comma] + ']'
            try:
                return json.loads(truncated)
            except json.JSONDecodeError:
                pass

        return None


# 全局单例
llm_service = LLMService()
