"""本地 LLM 客户端（Ollama 集成）

v3.0 支持国产开源模型本地运行：
- Qwen2-7B-Instruct（阿里 + 社区）
- ChatGLM3-6B（智谱 + 清华）
- Yi-6B-Chat（零一万物）
- DeepSeek-Coder-6.7B（代码）

v3.0 部署：
- Ollama（推荐）：https://ollama.com
- vLLM（高性能）
- llama.cpp（CPU 推理）

消费级 GPU 推荐：
- RTX 3060 12GB → 7B 模型（4-bit 量化）
- RTX 4090 24GB → 13B 模型 / 7B 全精度
- Apple M2/M3 → 7B 模型（Metal）
"""
from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

logger = logging.getLogger(__name__)


class OllamaClient:
    """Ollama 本地 LLM 客户端

    装 Ollama：https://ollama.com
    拉模型：ollama pull qwen2:7b
    启动：ollama serve（默认 :11434）
    """

    def __init__(self, model: str = "qwen2:7b-instruct", **kwargs):
        self.model = model
        self.base_url = os.getenv("MYHOME_LOCAL_LLM_URL", "http://localhost:11434")
        # v3.0 国产模型（按 priority 排序）
        self.supported_models = {
            "qwen2:7b-instruct": "通义千问 2 7B（阿里）",
            "qwen2:14b-instruct": "通义千问 2 14B（阿里）",
            "chatglm3:6b": "ChatGLM3 6B（智谱+清华）",
            "yi:6b-chat": "Yi 6B（零一万物）",
            "deepseek-coder:6.7b": "DeepSeek Coder 6.7B（代码）",
            "llama3.1:8b": "Llama 3.1 8B（Meta 国外）",
            "mistral:7b": "Mistral 7B（国外）",
        }

    def messages(
        self,
        system: str,
        messages: list,
        max_tokens: int = 1500,
        tools: list | None = None,
    ) -> Any:
        """Ollama /api/chat 调用（OpenAI 兼容）"""
        try:
            import requests
        except ImportError:
            return self._stub(system, messages)

        formatted = [{"role": "system", "content": system}] if system else []
        formatted.extend(messages)

        try:
            resp = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": formatted,
                    "stream": False,
                    "options": {"num_predict": max_tokens},
                },
                timeout=120,  # 本地推理慢
            )
            resp.raise_for_status()
            data = resp.json()
            text = data.get("message", {}).get("content", "（Ollama 无响应）")
            usage = {
                "input_tokens": data.get("prompt_eval_count", 0),
                "completion_tokens": data.get("eval_count", 0),
                "total_tokens": 0,
            }
            return self._wrap(text, usage)
        except Exception as e:
            logger.error(f"Ollama 调用失败: {e}")
            return self._stub(system, messages)

    def _wrap(self, text, usage):
        from ..agent.llm import LLMResponse
        return LLMResponse(
            text=text, tool_calls=[], stop_reason="end_turn",
            usage={
                "input_tokens": usage["input_tokens"],
                "completion_tokens": usage["completion_tokens"],
                "total_tokens": usage["input_tokens"] + usage["completion_tokens"],
            },
        )

    def _stub(self, system, messages):
        from ..agent.llm import LLMResponse, MockLLMClient
        logger.warning("Ollama 不可用，降级 mock")
        return MockLLMClient().messages(system=system, messages=messages)

    def list_models(self) -> list[str]:
        """列已下载的模型"""
        try:
            import requests
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return [m["name"] for m in resp.json().get("models", [])]
        except Exception:
            return []

    def pull(self, model: str) -> bool:
        """拉取模型（v3.0 首次安装用）"""
        try:
            import requests
            resp = requests.post(
                f"{self.base_url}/api/pull",
                json={"name": model},
                timeout=600,  # 模型下载慢
            )
            return resp.status_code == 200
        except Exception as e:
            logger.error(f"拉模型 {model} 失败: {e}")
            return False


# ============================================================
# 工厂
# ============================================================


def get_local_client(model: str = None) -> OllamaClient:
    """v3.0 工厂"""
    if not model:
        model = os.getenv("MYHOME_LOCAL_LLM_MODEL", "qwen2:7b-instruct")
    return OllamaClient(model=model)


# ============================================================
# 部署指南（v3.0 留作 v3.0.1 真实集成）
# ============================================================


DEPLOY_GUIDE = """
# v3.0 本地 LLM 部署（5 步）

1. 装 Ollama（macOS/Linux/Windows）
   curl -fsSL https://ollama.com/install.sh | sh

2. 拉国产模型（v3.0 推荐）
   ollama pull qwen2:7b-instruct       # 通义千问 2 7B（中文好）
   ollama pull chatglm3:6b              # 智谱 6B
   ollama pull yi:6b-chat               # 零一万物 6B

3. 启动 Ollama server（默认 :11434）
   ollama serve

4. 配 .env
   MYHOME_LOCAL_LLM_URL=http://localhost:11434
   MYHOME_LOCAL_LLM_MODEL=qwen2:7b-instruct

5. 接入 myhome-agent
   v3.0 路由自动选：隐私模式 → 本地 Qwen2
   对话隐私 / 老人数据 → 完全离线

# 性能（RTX 3060 12GB）
- Qwen2-7B Q4_K_M：~30 tokens/s
- ChatGLM3-6B Q4：~35 tokens/s
- 对话响应 < 1.5s（短输入）

# 内存占用
- 7B Q4 量化：~5GB VRAM
- 7B FP16：~14GB VRAM
- 7B FP32：~28GB VRAM
- CPU 推理（llama.cpp）：~8GB RAM（慢 5 倍）
"""