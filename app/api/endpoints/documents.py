from fastapi import APIRouter
from app.schemas.document import LayoutRequest
from app.core.llm import generate_layout_nodes

router = APIRouter()

@router.post("/layout")
def create_layout(request: LayoutRequest):
    """
    주제(topic)를 바탕으로 Gemini API를 통해 레이아웃 노드의 구조적 특성(카테고리, 중요도 등 8차원 속성)을 기획하여,
    추후 GNN 모델이 물리적 좌표와 크기를 예측할 수 있도록 기반이 되는 JSON을 리턴합니다.
    """

    result = generate_layout_nodes(request.topic)
    return result
