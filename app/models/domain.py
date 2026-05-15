from sqlalchemy import Column, String, Integer, Text, JSON, DateTime, ForeignKey, Numeric
from sqlalchemy.sql import func
from app.core.database import Base

class DocumentSource(Base):
    __tablename__ = "document_sources"

    source_id = Column(String(36), primary_key=True, index=True)
    # user_id는 사용자 관리가 제외되면서 외래키를 해제하거나 생략할 수 있습니다. 
    # 식별 용도로 남겨두기 위해 String으로만 선언했습니다.
    # user_id = Column(String(36), nullable=True) 
    topic = Column(String(255))
    content = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Document(Base):
    __tablename__ = "documents"

    doc_id = Column(String(36), primary_key=True, index=True)
    source_id = Column(String(36), ForeignKey("document_sources.source_id"))
    topic = Column(String(255))
    status = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Node(Base):
    __tablename__ = "nodes"

    node_id = Column(String(36), primary_key=True, index=True)
    doc_id = Column(String(36), ForeignKey("documents.doc_id"))
    category = Column(String(50))
    page_number = Column(Integer)
    x = Column(Numeric(10, 4))
    y = Column(Numeric(10, 4))
    width = Column(Numeric(10, 4))
    height = Column(Numeric(10, 4))

class Content(Base):
    __tablename__ = "contents"

    content_id = Column(String(36), primary_key=True, index=True)
    node_id = Column(String(36), ForeignKey("nodes.node_id"))
    content_body = Column(Text)
