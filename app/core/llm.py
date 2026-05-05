import json
import time
import os
from google import genai
from app.core.config import settings

# google api 네트워크 차단 해제
os.environ["GRPC_DNS_RESOLVER"] = "native"

# Configure Gemini API Client
client = genai.Client(api_key=settings.gemini_api_key)

def generate_layout_nodes(topic: str):
    prompt = f"""
You are an expert document layout designer. Based on the following document topic, generate a logical document structure layout.
Topic: {topic}

Return ONLY a JSON object with a "nodes" key. The "nodes" array should contain elements representing layout areas for the document.
Allowed types: Title, Section-header, Picture, Table, Formula, Text, List-item, Caption, Footnote

Since a separate GNN model will handle the positioning and sizing, you MUST set x, y, width, and height to null for every node.
Also, set content to null for every node.
Each node must have: type, content (null), x (null), y (null), width (null), height (null), z_index (int).

Format strictly as JSON. No markdown backticks, no explanations.
Example:
{{
  "nodes": [
    {{"type": "Title", "content": null, "x": null, "y": null, "width": null, "height": null, "z_index": 1}},
    {{"type": "Section-header", "content": null, "x": null, "y": null, "width": null, "height": null, "z_index": 1}}
  ]
}}
"""
    try:
        # 1. 텍스트 생성 지원 모델 동적 조회
        available_models = []
        for m in client.models.list():
            methods = getattr(m, 'supported_generation_methods', [])
            if methods and 'generateContent' in methods:
                available_models.append(m.name)
                
        # 만약 속성명이 변경되어 필터링이 안 될 경우를 대비해 폴백(Fallback)
        if not available_models:
            available_models = [m.name for m in client.models.list() if "gemini" in m.name.lower()]
            
    except Exception as e:
        return {"nodes": [], "error": f"모델 목록 조회 실패: {str(e.code)}"}
    
    # 2. 모델 순회
    for model_name in available_models:
        try:
            # 프롬프트 생성 및 API 호출
            
            response = client.models.generate_content(model=model_name, contents=prompt)
            text = response.text.strip()
            
            # Markdown 파싱 (백틱 제거)
            if text.startswith("```json"):
                text = text[7:]
            elif text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
                
            data = json.loads(text.strip())
            return data

        except Exception as e:
            print(f"[{model_name}] 에러 발생: {e.code}. 0.5초 후 다음 모델을 시도합니다.")
            time.sleep(0.5)
            continue
            
    # 4. 모든 모델 시도 실패 시
    return {"nodes": [], "error": "모든 가용 모델이 응답에 실패했습니다."}
