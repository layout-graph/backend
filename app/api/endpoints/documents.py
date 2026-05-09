from fastapi import APIRouter, HTTPException
from app.schemas.document import LayoutRequest, LayoutNode, LayoutPage, LayoutResponse
from app.core.llm import generate_layout_nodes
from app.core.graph_builder import build_graph_from_llm_json
from app.core.predictor import predict_layout

router = APIRouter()

@router.post("/layout", response_model=LayoutResponse)
def create_layout(request: LayoutRequest):
    """
    주제(topic)를 바탕으로:
    1. Gemini API(LLM)로 초기 레이아웃 구조를 기획합니다.
    2. LLM JSON을 GNN 입력 텐서로 변환합니다.
    3. LayoutGNN이 초기 좌표로부터의 Delta를 예측하여 최종 좌표를 반환합니다.
    4. LLM JSON에서 category를, 예측 결과에서 predicted_box를 추출하여
       역정규화 후 LayoutResponse(category + 픽셀 좌표)를 반환합니다.
    """
    # Step 1: LLM 호출
    llm_json = generate_layout_nodes(request.topic)

    if "error" in llm_json:
        raise HTTPException(status_code=502, detail=llm_json["error"])

    # Step 2: LLM JSON → GNN 입력 텐서
    try:
        graph_tensors = build_graph_from_llm_json(llm_json)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"그래프 변환 실패: {str(e)}")

    # Step 3: GNN 추론
    try:
        predictions = predict_layout(graph_tensors)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GNN 추론 실패: {str(e)}")

    # Step 4: category(LLM JSON) + predicted_box(예측 결과) 병합 → 역정규화 → LayoutResponse 반환
    pred_map = {p["id_box"]: p["predicted_box"] for p in predictions}

    pages_result = []
    id_counter = 0
    page_num = 1

    for page_key, page_data in llm_json.items():
        if not isinstance(page_data, dict):
            continue

        page_nodes = []
        for node in page_data.get("nodes", []):
            box = pred_map.get(id_counter, [0.0, 0.0, 0.0, 0.0])
            page_nodes.append(LayoutNode(
                category=node.get("category", "Text"),
                x=int(box[0] * request.canvas_width),
                y=int(box[1] * request.canvas_height),
                w=int(box[2] * request.canvas_width),
                h=int(box[3] * request.canvas_height),
            ))
            id_counter += 1

        pages_result.append(LayoutPage(page=page_num, nodes=page_nodes))
        page_num += 1

    return LayoutResponse(pages=pages_result)
