from pydantic import BaseModel

class LayoutRequest(BaseModel):
    topic: str
