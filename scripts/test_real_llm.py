"""v3.0.1 国产 LLM 真实集成 + 路由实测

前提：用户已配 DeepSeek（必选）+ Qwen / Kimi 等（可选）

用法：
    python scripts/test_real_llm.py
    # 跳过未配的 provider
    # 输出每个 provider 真实回复 + 用时 + token
"""
from __future__ import annotations

import os
import sys
import time
from typing import Any

sys.path.insert(0, ".")


def test_provider(name: str, client_factory) -> dict:
    """测试单个 provider"""
    t0 = time.time()
    try:
        client = client_factory()
        r = client.messages(
            system="你是 myhome-agent 家庭管家，回答简短中文（≤ 50 字）。",
            messages=[{"role": "user", "content": "你好，介绍下你自己。"}],
            max_tokens=200,
        )
        elapsed = time.time() - t0
        return {
            "name": name,
            "status": "✓",
            "latency_s": round(elapsed, 2),
            "text": r.text[:200] if hasattr(r, "text") else str(r)[:200],
            "input_tokens": r.usage.get("input_tokens", 0) if hasattr(r, "usage") else 0,
            "output_tokens": r.usage.get("completion_tokens", 0) if hasattr(r, "usage") else 0,
        }
    except Exception as e:
        return {
            "name": name,
            "status": "✗",
            "error": str(e)[:200],
            "latency_s": round(time.time() - t0, 2),
        }


def main():
    print("=" * 70)
    print("  v3.0.1 国产 LLM 真实集成 + 路由实测")
    print("=" * 70)
    print()

    # 5 provider
    results = []

    # 1. DeepSeek
    if os.getenv("DEEPSEEK_API_KEY"):
        from myhome_agent.agent.llm import DeepSeekLLMClient
        results.append(test_provider("DeepSeek-V3", lambda: DeepSeekLLMClient()))
    else:
        results.append({"name": "DeepSeek-V3", "status": "⏭ skipped (no key)"})

    # 2. Qwen（DashScope）
    if os.getenv("DASHSCOPE_API_KEY"):
        from myhome_agent.agent.dashscope_client import DashScopeClient
        results.append(test_provider("Qwen-Plus", lambda: DashScopeClient()))
    else:
        results.append({"name": "Qwen-Plus", "status": "⏭ skipped"})

    # 3. Zhipu (GLM-4-Plus)
    if os.getenv("ZHIPU_API_KEY"):
        from myhome_agent.agent.zhipu_client import ZhipuClient
        results.append(test_provider("Zhipu GLM-4-Plus", lambda: ZhipuClient()))
    else:
        results.append({"name": "Zhipu GLM-4-Plus", "status": "⏭ skipped"})

    # 4. Kimi (128K)
    if os.getenv("KIMI_API_KEY"):
        from myhome_agent.agent.kimi_client import KimiClient
        results.append(test_provider("Kimi 128K", lambda: KimiClient()))
    else:
        results.append({"name": "Kimi 128K", "status": "⏭ skipped"})

    # 5. model-info.forwe.store
    if os.getenv("MODEL_INFO_API_KEY"):
        from myhome_agent.agent.openai_compatible import ModelInfoClient
        results.append(test_provider("Model-Info 网关", lambda: ModelInfoClient()))
    else:
        results.append({"name": "Model-Info", "status": "⏭ skipped"})

    # 6. GPT-4o (国外补充)
    if os.getenv("OPENAI_API_KEY"):
        from myhome_agent.agent.openai_compatible import OpenAICompatibleClient
        results.append(test_provider("GPT-4o (国外)", lambda: OpenAICompatibleClient(
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4o",
        )))
    else:
        results.append({"name": "GPT-4o", "status": "⏭ skipped"})

    # 输出
    print(f"{'Provider':30} {'Status':6} {'Latency':10} {'Tokens':12} {'Sample Response'}")
    print("-" * 70)
    for r in results:
        name = r["name"][:30]
        status = r["status"]
        latency = f"{r.get('latency_s', 0)}s"
        if status == "✓":
            tokens = f"{r['input_tokens']}+{r['output_tokens']}"
            text = r.get("text", "")[:40].replace("\n", " ")
            print(f"{name:30} {status:6} {latency:10} {tokens:12} {text}")
        elif status == "⏭":
            print(f"{name:30} {status:6}")
        else:
            print(f"{name:30} {status:6} {r.get('error', '')[:60]}")

    # 路由决策测试
    print()
    print("=" * 70)
    print("  路由决策实测（任务类型 → 选哪个 provider）")
    print("=" * 70)
    from myhome_agent.agent.llm_router import LLMRouter, TaskType, PROVIDER_CAPS

    router = LLMRouter()
    stats = router.get_stats()
    print(f"\n可用 provider: {stats.get('available_cn', []) + stats.get('available_intl', [])}")
    print(f"预算月度: ${stats.get('budget_monthly_usd', 0)}")
    print(f"国产分配: {stats.get('cn_budget_pct', 0) * 100:.0f}% / 国外: {stats.get('intl_budget_pct', 0) * 100:.0f}%")
    print()
    print(f"{'Task Type':20} {'Provider':20} {'Model':25} {'Reason'}")
    print("-" * 90)
    for task_name in ["chat", "fallback", "vision", "planning", "long_context"]:
        decision = router.route(TaskType(task_name), context_size=2000)
        reason = decision.reason[:45] if hasattr(decision, "reason") else ""
        print(f"{task_name:20} {decision.provider:20} {decision.model[:24]:25} {reason}")


if __name__ == "__main__":
    main()