import json
import time
import os
from google import genai
from app.core.config import settings
from app.core.prompts import layout_nodes_prompt, content_for_nodes_prompt

# google api 네트워크 차단 해제
os.environ["GRPC_DNS_RESOLVER"] = "native"

# Configure Gemini API Client
client = genai.Client(api_key=settings.gemini_api_key)


# ─────────────────────────────────────────
# 내부 헬퍼 (모듈 외부에서 직접 호출 불필요)
# ─────────────────────────────────────────

def _get_available_models() -> list[str]:
    """텍스트 생성(generateContent)이 가능한 Gemini 모델 이름 목록을 반환한다."""
    try:
        available = [
            m.name for m in client.models.list()
            if getattr(m, "supported_generation_methods", None)
            and "generateContent" in m.supported_generation_methods
        ]
        # 속성명 변경 등으로 필터링이 안 될 경우 폴백
        if not available:
            available = [m.name for m in client.models.list() if "gemini" in m.name.lower()]
        return available
    except Exception as e:
        raise RuntimeError(f"모델 목록 조회 실패: {e}")


def _call_llm(prompt: str) -> dict:
    """
    가용 모델을 순회하며 LLM을 호출하고, JSON으로 파싱된 결과를 반환한다.

    Returns:
        파싱된 dict. 모든 모델 실패 시 {"error": str}.
    """
    try:
        models = _get_available_models()
    except RuntimeError as e:
        return {"error": str(e)}

    for model_name in models:
        try:
            response = client.models.generate_content(model=model_name, contents=prompt)
            text = response.text.strip()

            # Markdown 코드 펜스 제거
            if text.startswith("```json"):
                text = text[7:]
            elif text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]

            return json.loads(text.strip())

        except Exception as e:
            print(f"[{model_name}] 에러 발생: {e}. 0.5초 후 다음 모델을 시도합니다.")
            time.sleep(0.5)
            continue

    return {"error": "모든 가용 모델이 응답에 실패했습니다."}


# ─────────────────────────────────────────
# 공개 인터페이스
# ─────────────────────────────────────────

def generate_layout_nodes(topic: str) -> dict:
    """
    문서 주제를 바탕으로 GNN 입력용 레이아웃 구조 JSON을 생성한다.

    Returns:
        {"page1": {"nodes": [...]}, ...} 형태의 dict.
        실패 시 {"error": str}.
    """
    return _call_llm(layout_nodes_prompt(topic))


def generate_content_for_nodes(topic: str, original_content: str, nodes: list) -> dict:
    """
    각 노드의 category에 맞는 텍스트 콘텐츠를 LLM으로 생성한다.

    Args:
        topic: 문서 주제
        original_content: 원본 텍스트 (DocumentSource.content)
        nodes: [{"node_id": str, "category": str, "page": int}, ...]

    Returns:
        {node_id: content_body} 형태의 딕셔너리.
        실패 시 {"error": str}.
    """
    return _call_llm(content_for_nodes_prompt(topic, original_content, nodes))
