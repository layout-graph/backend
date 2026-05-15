from pydantic import BaseModel
from typing import List, Optional

class LayoutRequest(BaseModel):
    topic: str
    content: str
    canvas_width: int = 794    # 기본값: A4 너비 (px, 96dpi)
    canvas_height: int = 1123  # 기본값: A4 높이 (px, 96dpi)

class LayoutNode(BaseModel):
    category: str
    content: Optional[str] = None  # 레이아웃 초안 단계에서는 None, 최적화 후 채워짐
    x: int
    y: int
    w: int
    h: int

class LayoutPage(BaseModel):
    page: int
    nodes: List[LayoutNode]

class LayoutResponse(BaseModel):
    doc_id: str
    pages: List[LayoutPage]