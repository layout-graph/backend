from fastapi import APIRouter
from app.schemas.document import LayoutRequest
from app.core.llm import generate_layout_nodes

router = APIRouter()

@router.post("/layout")
def create_layout(request: LayoutRequest):
    """
    주제(topic)를 바탕으로 Gemini API를 통해 레이아웃 노드를 기획하고, 
    좌표와 크기는 null로 지정하여 GNN 모델 연계를 위한 JSON을 리턴합니다.
    """

    result = generate_layout_nodes(request.topic)
    return result
