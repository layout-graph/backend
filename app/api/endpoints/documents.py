from sqlalchemy import null
import uuid
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.schemas.document import LayoutRequest, LayoutNode, LayoutPage, LayoutResponse
from app.core.llm import generate_layout_nodes, generate_content_for_nodes
from app.core.graph_builder import build_graph_from_llm_json
from app.core.predictor import predict_layout
from app.core.database import get_db
from app.models.domain import DocumentSource, Document, Node, Content

router = APIRouter()

@router.post("/layout", response_model=LayoutResponse)
def create_layout(request: LayoutRequest, db: Session = Depends(get_db)):
    """
    주제(topic)를 바탕으로:
    1. 원시 데이터를 DocumentSource에 저장
    2. Gemini API(LLM)로 초기 레이아웃 구조 기획
    3. GNN으로 최종 좌표 예측
    4. 결과를 Document 및 Node 테이블에 저장 후 클라이언트에 반환
    """
    # Step 1: DocumentSource 생성 (원시 데이터 저장)
    source_id = str(uuid.uuid4())
    db_source = DocumentSource(
        source_id=source_id,
        topic=request.topic,
        content=request.content
    )
    db.add(db_source)
    db.commit()
    
    # Step 2: LLM 호출
    llm_json = generate_layout_nodes(request.topic)

    if "error" in llm_json:
        raise HTTPException(status_code=502, detail=llm_json["error"])

    # Step 3: LLM JSON → GNN 입력 텐서
    try:
        graph_tensors = build_graph_from_llm_json(llm_json)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"그래프 변환 실패: {str(e)}")

    # Step 4: GNN 추론
    try:
        predictions = predict_layout(graph_tensors)
    except Exception as e: 
        raise HTTPException(status_code=500, detail=f"GNN 추론 실패: {str(e)}")

    # Step 5: Document 레코드 생성 및 저장
    doc_id = str(uuid.uuid4())
    db_doc = Document(
        doc_id=doc_id,
        source_id=source_id,
        topic=request.topic,
        status="LAYOUT_DONE"
    )
    db.add(db_doc)
    db.commit()

    # Step 6: 예측 결과 맵핑 및 Node DB 저장 준비
    pred_map = {p["id_box"]: p["predicted_box"] for p in predictions}

    pages_result = []
    db_nodes = []
    id_counter = 0
    page_num = 1

    for page_key, page_data in llm_json.items():
        if not isinstance(page_data, dict):
            continue

        page_nodes = []
        for node in page_data.get("nodes", []):
            box = pred_map.get(id_counter, [0.0, 0.0, 0.0, 0.0])
            category = node.get("category", "Text")
            
            # 역정규화 (픽셀 좌표로 변환)
            x_px = int(box[0] * request.canvas_width)
            y_px = int(box[1] * request.canvas_height)
            w_px = int(box[2] * request.canvas_width)
            h_px = int(box[3] * request.canvas_height)
            
            # DB용 Node 객체 생성
            node_id = str(uuid.uuid4())
            db_node = Node(
                node_id=node_id,
                doc_id=doc_id,
                category=category,
                page_number=page_num,
                x=x_px,
                y=y_px,
                width=w_px,
                height=h_px,
            )
            db_nodes.append(db_node)
            
            # 응답용 스키마 생성
            page_nodes.append(LayoutNode(
                category=category,
                page=page_num,
                content=None,
                x=x_px,
                y=y_px,
                w=w_px,
                h=h_px,
            ))
            id_counter += 1

        pages_result.append(LayoutPage(page=page_num, nodes=page_nodes))
        page_num += 1

    # DB에 생성된 모든 노드를 일괄 저장 (bulk insert 효과)
    if db_nodes:
        db.add_all(db_nodes)
        db.commit()

    # Step 7: LayoutResponse 반환 (발급된 doc_id 포함)
    return LayoutResponse(doc_id=doc_id, pages=pages_result)


@router.post("/optimize/{doc_id}", response_model=LayoutResponse)
def optimize_layout(doc_id: str, db: Session = Depends(get_db)):
    """
    생성된 레이아웃을 바탕으로:
    1. DB에서 Document, Node 목록, DocumentSource 조회
    2. LLM으로 노드별 최적화 콘텐츠 생성
    3. contents 테이블에 저장
    4. 노드 좌표 + 콘텐츠 결합 후 LayoutResponse 반환
    """
    # Step 1: DB 조회
    doc = db.query(Document).filter(Document.doc_id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail=f"doc_id '{doc_id}' 에 해당하는 문서를 찾을 수 없습니다.")

    source = db.query(DocumentSource).filter(DocumentSource.source_id == doc.source_id).first()
    nodes = db.query(Node).filter(Node.doc_id == doc_id).all()

    if not nodes:
        raise HTTPException(status_code=400, detail="해당 문서에 연결된 노드가 없습니다. 먼저 레이아웃을 생성하세요.")

    # Step 2: LLM 호출 — 노드별 콘텐츠 생성
    node_dicts = [
        {"node_id": n.node_id, "category": n.category, "page": n.page_number}
        for n in nodes
    ]
    original_content = source.content if source else ""
    llm_result = generate_content_for_nodes(doc.topic, original_content, node_dicts)

    if "error" in llm_result:
        raise HTTPException(status_code=502, detail=f"LLM 콘텐츠 생성 실패: {llm_result['error']}")

    # Step 3: contents 테이블에 저장
    for node in nodes:
        content_body = llm_result.get(node.node_id, "")
        db_content = Content(
            content_id=str(uuid.uuid4()),
            node_id=node.node_id,
            content_body=content_body,
        )
        db.add(db_content)

    # Document 상태 업데이트
    doc.status = "OPTIMIZED"
    db.commit()

    # Step 4: 응답 구성 — 노드를 page_number 기준으로 그룹화
    pages_dict: dict[int, list] = {}
    for node in nodes:
        pages_dict.setdefault(node.page_number, []).append(node)

    pages_result = []
    for page_num, page_nodes in sorted(pages_dict.items()):
        layout_nodes = [
            LayoutNode(
                category=node.category,
                content=llm_result.get(node.node_id, ""),
                x=int(node.x),
                y=int(node.y),
                w=int(node.width),
                h=int(node.height),
            )
            for node in page_nodes
        ]
        pages_result.append(LayoutPage(page=page_num, nodes=layout_nodes))

    return LayoutResponse(doc_id=doc_id, pages=pages_result)
