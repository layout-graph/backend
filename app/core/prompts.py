"""
LLM 프롬프트 템플릿 모음.

각 함수는 필요한 변수를 인자로 받아 완성된 프롬프트 문자열을 반환한다.
실제 LLM 호출 로직은 llm.py 에서 담당한다.
"""

import json


def layout_nodes_prompt(topic: str) -> str:
    """
    GNN 입력용 레이아웃 구조 JSON을 생성하기 위한 프롬프트.

    Args:
        topic: 문서 주제

    Returns:
        완성된 프롬프트 문자열
    """
    return f"""
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


def content_for_nodes_prompt(topic: str, original_content: str, nodes: list) -> str:
    """
    노드별 최적화 콘텐츠를 생성하기 위한 프롬프트.

    Args:
        topic: 문서 주제
        original_content: 원본 텍스트 (DocumentSource.content)
        nodes: [{"node_id": str, "category": str, "page": int}, ...]

    Returns:
        완성된 프롬프트 문자열
    """
    nodes_json = json.dumps(nodes, ensure_ascii=False, indent=2)

    return f"""
You are an expert document content writer.
Based on the document topic and original source content below, generate appropriate text for each layout node.

Document Topic: {topic}

Original Source Content:
{original_content}

Layout Nodes (JSON array — each has node_id, category, page):
{nodes_json}

Generation rules per category:
- Title          : Concise, impactful document title.
- Section-header : Clear section heading relevant to the topic.
- Text           : 2-4 sentences of paragraph text that fits the document flow.
- List-item      : A single bullet-point item (no leading dash).
- Caption        : A brief descriptive caption (1 sentence).
- Footnote       : A short footnote or reference note.
- Table          : A plain-text representation of a small relevant table.
- Formula        : A formula or equation string.
- Picture        : A concise image description for visual search (e.g. "bar chart showing quarterly revenue growth").

Return ONLY a flat JSON object where:
- Each KEY is the node_id string.
- Each VALUE is the generated content string for that node.

No markdown, no code fences, no extra keys.

Example:
{{
  "uuid-aaa": "Quarterly Revenue Report 2024",
  "uuid-bbb": "Revenue grew steadily throughout the year, driven by..."
}}
"""
