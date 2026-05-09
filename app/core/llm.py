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

Return ONLY a JSON object representing the logical layout structure for the document, grouped by pages.
Use keys like "page1", "page2" for each page, and under each page key, provide a "nodes" array containing the layout elements.
A downstream Graph Neural Network (GNN) will use these features as an initial guess to refine and predict the exact physical coordinates.
Therefore, for each node, you MUST provide the following 8 properties ALONG WITH an initial guess for the physical bounding box:
1. "category": String. Allowed values: Title, Section-header, Picture, Table, Formula, Text, List-item, Caption, Footnote
2. "importance": Float (0.0 ~ 1.0). The expected relative visual area this node should take compared to the whole document.
3. "text_length": Float (0.0 ~ 1.0). The normalized expected text length (0 for non-text).
4. "aspect_ratio": Float. The expected aspect ratio (Width / Height).
5. "reading_order": Integer. The sequence order in the document (0, 1, 2, ...).
6. "has_paragraph": Integer. 1 if the node contains paragraph text, 0 otherwise.
7. "tree_depth": Integer. The depth in the logical document hierarchy (e.g., Document root=0, Title=1, Text=2).
8. "children_count": Integer. The expected number of child nodes under this node in the hierarchy.
9. "box": Array of 4 Floats [x, y, width, height] normalized between 0.0 and 1.0. This is your initial rough estimation of the layout position.

Format strictly as JSON. No markdown backticks, no explanations.
Example:
{{
  "page1": {{
    "nodes": [
      {{"category": "Title", "importance": 0.1, "text_length": 0.2, "aspect_ratio": 5.0, "reading_order": 0, "has_paragraph": 1, "tree_depth": 0, "children_count": 0, "box": [0.1, 0.05, 0.8, 0.1]}},
      {{"category": "Text", "importance": 0.2, "text_length": 0.8, "aspect_ratio": 1.0, "reading_order": 1, "has_paragraph": 1, "tree_depth": 1, "children_count": 0, "box": [0.1, 0.2, 0.8, 0.3]}}
    ]
  }},
  "page2": {{
    "nodes": [
      {{"category": "Section-header", "importance": 0.05, "text_length": 0.3, "aspect_ratio": 4.0, "reading_order": 2, "has_paragraph": 1, "tree_depth": 0, "children_count": 2, "box": [0.1, 0.05, 0.5, 0.05]}}
    ]
  }}
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
        return {"error": f"모델 목록 조회 실패: {str(e.code)}"}
    
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
    return {"error": "모든 가용 모델이 응답에 실패했습니다."}
