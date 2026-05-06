# 1. **API 설계**

| **HTTP Method** | **URL Path**                        | **기능 설명**                                                     |
| --------------- | ----------------------------------- | ----------------------------------------------------------------- |
| **POST**        | `/api/documents/layout`             | 원시 자료 업로드 및 GNN 기반 레이아웃 초안 생성                   |
| **GET**         | `/api/documents/{doc_id}/optimize`  | 레이아웃 확정 후 LLM/CLIP 기반 최종 콘텐츠 최적화                 |
| **GET**         | `/api/v1/documents/{doc_id}`        | 최적화가 완료된 단일 JSON 소스 조회 및 실시간 문서 렌더링         |
| **PATCH**       | `/api/v1/documents/{doc_id}/sync`   | 프리뷰 수치 수정 시 단일 JSON 소스 기반 텍스트-차트 실시간 동기화 |
| **GET**         | `/api/v1/documents/{doc_id}/export` | 최종 완성된 문서를 PDF 또는 HTML 규격으로 내보내기                |

#### 레이아웃 노드 생성

> 원시 자료 업로드 및 GNN 기반 레이아웃 초안 생성

- method : POST
- url : `/api/documents/layout`
- **Request** (JSON):
  ```json
  {
    "topic": "문서의 주제 (예: 스마트팩토리 분석)"
  }
  ```
- **Response** (JSON):
  ```json
  {
    "nodes": [
      {
        "type": "TITLE",
        "content": null,
        "x": null,
        "y": null,
        "width": null,
        "height": null,
        "z_index": 1
      }
    ]
  }
  ```

#### 사용자 입력 최적화

> 레이아웃 확정 후 LLM/CLIP 기반 최종 콘텐츠 최적화

- method : GET
- url : `/api/documents/opimize/{doc_id}`

#### 렌더링

> 최적화가 완료된 단일 JSON 소스 조회 및 실시간 문서 렌더링

- metho : GET
- url : /api/documents/{doc_id}

#### 문서 다운로드

> 최종 완성된 문서를 PDF 또는 HTML 규격으로 내보내기

- method : GET
- url : /api/documents/export/{doc_id}

# database

![[스크린샷 2026-04-28 오후 11.20.04.png]]

## 1. 사용자 및 인증 관리

### `users`

**설명**: 사용자 기본 정보

- `user_id` (`varchar(36)`): pk
- `email` (`varchar(255)`) : google 이메일
- `name` (`varchar(100)`) : 사용자 이름
- `created_at` (`timestamp`) : 가입일

### `accounts`

**설명**: Google OAuth 인증 정보

- `account_id` (`varchar(36)`) : pk
- `user_id` (`varchar(36)`): 소속 사용자
- `provider` (`varchar(50)`): 인증 제공자 (예: 'google')
- `provider_account_id` (`varchar(255)`): 구글 고유 ID
- `access_token` (`text`) : 로그인 관리
- `refresh_token` (`text`) : 로그인 관리
- `expires_at` (`timestamp`) : 로그인 만료

## 2. 시스템의 중심: 수치 데이터 원본 (Single Source of Truth)

### `document_json_sources`

**설명**: 모든 생성물의 근간이 되는 데이터 허브

- `source_id` (`varchar(36)`): 데이터 소스 고유 ID
- `user_id` (`varchar(36)`): 데이터의 소유자
- `json_data` (`json`): 정제된 핵심 수치 데이터 원본
- `created_at` (`timestamp`) : 생성일

## 3. 원시 자료 (JSON Source에 귀속된 입력 데이터)

### `data`

**설명**: JSON 데이터를 생성하기 위해 사용된 원재료

- `data_id` (`varchar(36)`) : pk
- `source_id` (`varchar(36)`): 해당 데이터가 정제되어 들어간 JSON 소스
- `type` (`varchar(20)`): IMAGE, TEXT, CSV
- `content` (`text`): 추출된 텍스트 원문
- `file_path` (`varchar(512)`): 저장소 경로
- `created_at` (`timestamp`) : 생성일

## 4. 보고서 본체 (JSON Source에서 파생된 인스턴스)

### `documents`

**설명**: 데이터 소스를 바탕으로 구성된 개별 보고서

- `doc_id` (`varchar(36)`) : pk
- `source_id` (`varchar(36)`): 이 보고서가 참조하는 원천 데이터
- `title` (`varchar(255)`) : 조회를 위해 제목저장
- `topic` (`varchar(255)`) : 조회를 위해 주제저장
- `status` (`varchar(50)`): LAYOUT_DONE, COMPLETED
- `graph` (`json`): GNN 모델의 레이아웃 논리 구조
- `created_at` (`timestamp`) : 생성일
- `updated_at` (`timestamp`) : 업데이트일

## 5. 레이아웃 노드 (Document에 소속된 공간 정보)

### `nodes`

**설명**: 문서 내 시각적 구역 정보

- `node_id` (`varchar(36)`) : pk
- `doc_id` (`varchar(36)`): 소속 보고서
- `type` (`varchar(50)`): TITLE, SECTION, IMAGE_AREA, CHART_AREA
- `x` (`decimal(10,4)`) : 생성된 x좌표
- `y` (`decimal(10,4)`) : 생성된 y좌표
- `width` (`decimal(10,4)`) : 생성된 width 크기
- `height` (`decimal(10,4)`) : 생성된 height 크기
- `z_index` (`int`) : node 순서 우선순위

## 6. 최종 콘텐츠 (Node에 매핑된 최종 결과물)

### `contents`

**설명**: 실제 렌더링될 콘텐츠 조각

- `block_id` (`varchar(36)`) : pk
- `node_id` (`varchar(36)`): 공간 노드와 1:1 매핑
- `content_type` (`varchar(20)`): TEXT, IMAGE, CHART
- `content_body` (`text`): 가공된 최종 텍스트 또는 이미지 경로
