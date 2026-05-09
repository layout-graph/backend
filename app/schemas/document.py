from pydantic import BaseModel
from typing import List

class LayoutRequest(BaseModel):
    topic: str
    canvas_width: int = 794    # 기본값: A4 너비 (px, 96dpi)
    canvas_height: int = 1123  # 기본값: A4 높이 (px, 96dpi)

class LayoutNode(BaseModel):
    category: str
    x: int
    y: int
    w: int
    h: int

class LayoutPage(BaseModel):
    page: int
    nodes: List[LayoutNode]

class LayoutResponse(BaseModel):
    pages: List[LayoutPage]
