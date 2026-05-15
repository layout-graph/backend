
# ARCHITECTURE

> 데이터 + 주제 입력 -> 레이아웃 생성 ->  렌더링 -> 최적화 -> 렌더링

# API

| **HTTP Method** | **URL Path**                        | **기능 설명**                                |
| --------------- | ----------------------------------- | ---------------------------------------- |
| **POST**        | `/api/documents/layout`             | 원시 자료 업로드 및 GNN 기반 레이아웃 초안 생성            |
| **POST**        | `/api/documents/optimize/{doc_id}`  | 레이아웃 확정 후 LLM/CLIP 기반 최종 콘텐츠 최적화         |
| **GET**         | `/api/v1/documents/{doc_id}`        | 최적화가 완료된 단일 JSON 소스 조회 및 실시간 문서 렌더링      |
| **PATCH**       | `/api/v1/documents/{doc_id}/sync`   | 프리뷰 수치 수정 시 단일 JSON 소스 기반 텍스트-차트 실시간 동기화 |
| **GET**         | `/api/v1/documents/{doc_id}/export` | 최종 완성된 문서를 PDF 또는 HTML 규격으로 내보내기         |


#### 레이아웃 노드 생성

> 원시 자료 업로드 및 GNN 기반 레이아웃 초안 생성

- method : POST
- url : `/api/documents/layout`
- **Request** (JSON):
  ```json
  {
    "topic": "보고서 주제",
    "content": "보고서 내용"
  }
  ```
- **Response** (JSON):
  ```json
  {
	  "doc_id": str,
	  "pages": [
		  {
			  "page": int,
			  "nodes": [
				  {
					  "cetegory": str,
					  "content": null,
					  "x": int,
					  "y": int,
					  "w": int,
					  "h": int
				  },
				  {
					  "cetegory": str,
					  "content": null,
					  "x": int,
					  "y": int,
					  "w": int,
					  "h": int
				  }
			  ]
		  }
	  ]
  }
  ```
  *(참고: GNN 모델이 물리적 좌표를 더 정교하게 예측할 수 있도록, LLM이 8차원의 구조적 속성뿐 아니라 대략적인 초기 좌표인 `box` 예측값을 함께 반환합니다. GNN의 총 입력 노드 피처는 20차원입니다.)*

#### 사용자 입력 최적화

> 레이아웃 확정 후 LLM/CLIP 기반 최종 콘텐츠 최적화, 이미 생성되어있는 경우 업데이트

- method : POST
- url : `/api/documents/opimize/{doc_id}`


- **Response** (JSON):
```json
 {
	  "doc_id": str,
	  "pages": [
		  {
			  "page": 1,
			  "nodes": [
				  {
					  "cetegory": "Title",
					  "content": "최적화된 내용",
					  "x": int,
					  "y": int,
					  "w": int,
					  "h": int
				  },
				  {
					  "cetegory": "Text",
					  "content": "최적화된 내용",
					  "x": int,
					  "y": int,
					  "w": int,
					  "h": int
				  }
			  ]
		  }
	  ]
  }
```

#### 렌더링

> 최적화가 완료된 단일 JSON 소스 조회 및 실시간 문서 렌더링

- metho : GET
- url : /api/documents/{doc_id}

```json
 {
	  "doc_id": str,
	  "pages": [
		  {
			  "page": 1,
			  "nodes": [
				  {
					  "cetegory": "Title",
					  "content": "최적화된 내용",
					  "x": int,
					  "y": int,
					  "w": int,
					  "h": int
				  },
				  {
					  "cetegory": "Text",
					  "content": "최적화된 내용",
					  "x": int,
					  "y": int,
					  "w": int,
					  "h": int
				  }
			  ]
		  }
	  ]
  }
```

#### 문서 다운로드

> 최종 완성된 문서를 PDF 또는 HTML 규격으로 내보내기

- method : GET
- url : /api/documents/export/{doc_id}

# DATABASE

![[스크린샷 2026-04-28 오후 11.20.04.png]]
*위 사진과과 실제 구현 테이블이 살짝씩 다름*

## 2. 시스템의 중심 데이터 원본 (Single Source of Truth)

### `document_sources`

**설명**: 모든 생성물의 근간이 되는 데이터 허브

- `source_id`: 데이터 소스 고유 ID
- ~~user_id : 데이터의 소유자
- `topic` : 보고서 주제
- `content` : 보고서 내용
- `created_at` : 생성일

## 4. 보고서 본체 (JSON Source에서 파생된 인스턴스)

### `documents`

**설명**: 데이터 소스를 바탕으로 구성된 개별 보고서

- `doc_id` : 레이아웃 id
- `source_id` : 이 보고서가 참조하는 원천 데이터
- `topic`  : 조회를 위한 주제
- `status` : 레이아웃 상태(LAYOUT_DONE, OPTIMIZED)
- `created_at` : 생성일
- `updated_at` : 업데이트일

## 5. 레이아웃 노드 (Document에 소속된 공간 정보)

### `nodes`

**설명**: 문서 내 시각적 구역 정보

- `node_id` : 노드 id
- `doc_id` : 소속 보고서
- `type` :노드 타입(Title, Text ...)
- `page_number` : 소속 페이지 
- `reading_order`: 읽기 순서
- `text_length` : 예상 텍스트 길이
- `x` : 생성된 x좌표
- `y` : 생성된 y좌표
- `w`  : 생성된 width 크기
- `h`  : 생성된 height 크기

## 6. 최종 콘텐츠 (Node에 매핑된 최종 결과물)

### `contents`

**설명**: 실제 렌더링될 콘텐츠 조각

- `content_id` : 내용 id
- `node_id` : 노드와 1:1 매핑
- `content_body`: 가공된 최종 텍스트 또는 이미지 경로

*구현되지 않은 테이블*
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


