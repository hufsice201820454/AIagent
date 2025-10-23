# -*- coding: utf-8 -*-
"""
LLM helper

- OPENAI_API_KEY를 evagent/.env 또는 환경변수에서 로드 후, 간단한 Markdown 생성 헬퍼 제공
- openai 패키지가 없거나 네트워크가 막힌 환경에서는 예외를 던진다(상위에서 폴백 처리)
"""
from __future__ import annotations

import os


def _load_env_from_dotenv() -> None:
    if os.getenv("OPENAI_API_KEY"):
        return
    try:
        base = os.path.dirname(os.path.abspath(__file__))
        env = os.path.normpath(os.path.join(base, "..", ".env"))
        if os.path.isfile(env):
            with open(env, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    k = k.strip(); v = v.strip().strip('"').strip("'")
                    if k and v and not os.getenv(k):
                        os.environ[k] = v
    except Exception:
        pass


_load_env_from_dotenv()


def generate_markdown(prompt: str, *, model: str = "gpt-4o-mini") -> str:
    """Prompt를 Markdown 문자열로 생성.

    openai 라이브러리 존재 및 OPENAI_API_KEY 필요.
    상위 호출부에서 예외를 캐치해 폴백(HTML 스켈레톤) 처리한다.
    """
    try:
        from openai import OpenAI  # type: ignore
    except Exception as e:
        raise RuntimeError("openai library not available") from e

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")

    client = OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "당신은 전문 애널리스트입니다. 한국어로만 답하고, 주어진 데이터만 근거로 작성합니다."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )
    content = resp.choices[0].message.content or ""
    return content

