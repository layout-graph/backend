import os
import sys
import glob
import torch

# model/ 패키지를 import하기 위한 경로 설정
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if os.path.join(_PROJECT_ROOT, 'model', 'layout') not in sys.path:
    sys.path.insert(0, os.path.join(_PROJECT_ROOT, 'model', 'layout'))

from model import LayoutGNN

# 체크포인트 디렉토리: back/checkpoints/
CHECKPOINT_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'checkpoints')


def _load_latest_checkpoint() -> LayoutGNN:
    """checkpoints/ 디렉토리에서 가장 최신 .pt 파일을 자동으로 찾아 모델에 로드합니다."""
    pt_files = glob.glob(os.path.join(CHECKPOINT_DIR, '*.pt'))
    if not pt_files:
        raise FileNotFoundError(f"체크포인트 파일이 없습니다: {CHECKPOINT_DIR}")

    # 파일명의 epoch 번호 기준 가장 최신 파일 선택
    latest = max(pt_files, key=lambda f: os.path.getmtime(f))

    model = LayoutGNN(in_channels=20, out_channels=4, edge_dim=15)
    state_dict = torch.load(latest, map_location=torch.device('cpu'))
    model.load_state_dict(state_dict)
    model.eval()

    print(f"[predictor] 체크포인트 로드 완료: {os.path.basename(latest)}")
    return model


def predict_layout(graph_tensors: dict) -> list:
    """
    GNN 모델에 그래프 텐서를 입력하여 노드별 최종 좌표를 예측합니다.

    Args:
        graph_tensors: build_graph_from_llm_json()의 반환값

    Returns:
        [{"id_box": int, "predicted_box": [x, y, w, h]}, ...]
    """
    x = graph_tensors["x"]
    adj_vis = graph_tensors["adj_vis"]
    attr_vis = graph_tensors["attr_vis"]
    adj_hier = graph_tensors["adj_hier"]
    attr_hier = graph_tensors["attr_hier"]
    nodes = graph_tensors["nodes"]

    model = _load_latest_checkpoint()

    with torch.no_grad():
        # 모델은 내부에서 initial_coords + delta를 계산해 최종 좌표를 반환
        predicted = model(x, adj_vis, attr_vis, adj_hier, attr_hier)  # [N, 4]

    results = []
    for i, node in enumerate(nodes):
        box = predicted[i].tolist()
        # 값을 0~1 범위로 클리핑
        box = [max(0.0, min(1.0, v)) for v in box]
        results.append({
            "id_box": node.get("id_box", i),
            "predicted_box": box,   # [x, y, w, h] 정규화 좌표
        })

    return results
