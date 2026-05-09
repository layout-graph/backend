import sys
import os

# model/ 패키지를 import하기 위한 경로 설정
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, os.path.join(_PROJECT_ROOT, 'model', 'graph'))
    sys.path.insert(0, os.path.join(_PROJECT_ROOT, 'model', 'layout'))

# pyrefly: ignore [missing-import]
from generate_adj import parse_nodes, build_visibility_edges, build_hierarchical_edges
# pyrefly: ignore [missing-import]
from generate_attr import calculate_edge_attributes
# pyrefly: ignore [missing-import]
from generate_feat import generate_features
# pyrefly: ignore [missing-import]
from tensor_utils import to_tensors


def _flatten_llm_nodes(llm_json: dict) -> list:
    """LLM JSON의 페이지별 nodes를 flat한 단일 리스트로 변환합니다."""
    flat = []
    id_counter = 0
    for page_key, page_data in llm_json.items():
        if not isinstance(page_data, dict):
            continue
        for node in page_data.get("nodes", []):
            flat.append({
                "id": id_counter,
                "category": node.get("category", "Text"),
                "box": node.get("box", [0.1, 0.1, 0.8, 0.1]),
                "importance": node.get("importance", 0.1),
                "text_length": node.get("text_length", 0.0),
                "aspect_ratio": node.get("aspect_ratio", 1.0),
                "reading_order": node.get("reading_order", id_counter),
                "has_paragraph": node.get("has_paragraph", 0),
                "tree_depth": node.get("tree_depth", 0),
                "children_count": node.get("children_count", 0),
            })
            id_counter += 1
    return flat


def _calc_edge_attrs(flat_nodes: list, id_vis: list, id_hier: list) -> tuple:
    """엣지 쌍 리스트에 대해 15차원 엣지 속성을 계산합니다."""
    nodes_dict = {n['id']: n for n in flat_nodes}

    def convert(edge_list):
        return [
            {"edge": [u, v], "attr": calculate_edge_attributes(nodes_dict[u], nodes_dict[v])}
            for u, v in edge_list
            if u in nodes_dict and v in nodes_dict
        ]

    return convert(id_vis), convert(id_hier)


def build_graph_from_llm_json(llm_json: dict) -> dict:
    """
    LLM JSON → GNN 입력 텐서로 변환하는 오케스트레이터.

    Returns:
        {"x", "adj_vis", "attr_vis", "adj_hier", "attr_hier", "nodes"}
    """
    # 1. 페이지별 → 단일 flat 리스트
    flat_nodes = _flatten_llm_nodes(llm_json)

    if not flat_nodes:
        raise ValueError("LLM JSON에서 변환할 노드가 없습니다.")

    # 2. 엣지 생성 (통합 generate_adj 사용)
    adj_nodes = parse_nodes(flat_nodes)
    vis_idx = build_visibility_edges(adj_nodes, max_dx=0.8, max_dy=0.9)
    hier_idx = build_hierarchical_edges(adj_nodes, vis_idx)

    id_vis = [(adj_nodes[u]['id'], adj_nodes[v]['id']) for u, v in vis_idx]
    id_hier = [(adj_nodes[u]['id'], adj_nodes[v]['id']) for u, v in hier_idx]

    # 3. 엣지 속성 계산 (통합 generate_attr 사용)
    vis_attrs, hier_attrs = _calc_edge_attrs(flat_nodes, id_vis, id_hier)

    # 4. 피처 추출 (통합 generate_feat 사용)
    feat_list = generate_features(flat_nodes, id_hier)

    if not feat_list:
        raise ValueError("유효한 카테고리의 노드가 없어 피처를 추출할 수 없습니다.")

    # 5. 텐서 변환 (통합 tensor_utils 사용)
    return to_tensors(feat_list, id_vis, id_hier, vis_attrs, hier_attrs)
