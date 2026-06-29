# 🔌 Webtoon Studio → WeRUB(blog) 통합 스펙

> 웹툰 스튜디오를 **별도 앱이 아니라 WeRUB 커뮤니티 플랫폼의 `blog`(Next.js) 소설 기능의 형제 기능**으로 합류시킨다.
> 컨셉: **소설 → 웹툰 각색(adaptation)**. 이미 시스템에 있는 소설(챕터/씬/캐릭터/플롯)을 웹툰 컷으로 재구성.
> 화면 설계(6단계 UX)는 [`webtoon-studio-ux.md`](webtoon-studio-ux.md)를 그대로 따르되, **아키텍처는 아래로 대체**한다.
> 작업은 WeRUB repo의 Claude Code CLI에서 진행. 이 문서가 그 작업 지시서다.

---

## 0. 대상 코드베이스 사실 (조사 결과)

- repo: `weruby-co-kr/WeRUB` (private, 모노레포). 웹앱은 **`blog/`** = Next.js 16 + React 19 + Prisma 7 + next-auth 5 + TS.
- 에디터/그래프 자산 보유: **`@tiptap/react`**(글쓰기), **`@xyflow/react`**(노드 그래프=플롯/관계도).
- 소설 기능 = 이미 풀 스튜디오:
  - UI: `blog/src/app/(admin)/dashboard/novels/[id]/{page,characters,world,plot,revise,analysis,stats,cli,write/[chapterId]}/page.tsx`
  - 탭: `blog/src/components/novel/NovelSubNav.tsx` (대시보드/캐릭터/세계관/플롯/퇴고/분석/통계/AI집필)
  - API: `blog/src/app/api/novels/[id]/{chapters,worlds,characters,plots,scenes,stats,ai,export}/...`
- **GPU 서버 호출 = 이미 정립됨**:
  - `blog/src/lib/gpu-proxy.ts` → `gpuFetch(path,{method,body,timeout})`. `GPU_API_URL`(기본 `https://ollama.weve.io.kr` = 8585 서버) + Bearer 키.
  - 텍스트 프록시: `api/ai/novel/[...path]` → GPU `/api/novel/*`, `api/ai/story/[...path]` → `/api/story/*`.
  - **이미지 렌더 프록시 = 이미 SSE 오케스트레이션 구현**: `api/ai/generate-image/route.ts` — `POST /api/image/generate` → `job_id` → `/api/image/status/{id}` 2초 폴링(최대 60회) → 큐 위치/렌더링/완료를 **SSE `send("progress",…)`**로 스트리밍. `api/ai/image-proxy?f={filename}` = GPU 이미지 뷰 프록시(인증 주입).

> 핵심: **SSH·Mac 클라이언트·base64 자가완결 HTML 불필요.** 블로그 서버가 HTTPS로 GPU를 호출하고, 패널은 GPU가 Wasabi S3에 올린 URL을 그대로 참조한다. 검증된 `weru_imagegen.py`/`build_viewer.py` 로직은 **TS로 이식**(아래).

---

## 1. 통합 위치 — 소설의 형제 탭 "웹툰"

`NovelSubNav.tsx`에 탭 1개 추가:

```ts
{ href: "/webtoon", label: "웹툰", icon: Clapperboard },
```

→ 진입점 `dashboard/novels/[id]/webtoon`. "이 소설을 웹툰으로 각색" 흐름이 소설 옆에 자연스럽게 붙는다.

---

## 2. 추가할 파일 트리 (App Router 컨벤션 준수)

### UI 페이지 — `blog/src/app/(admin)/dashboard/novels/[id]/webtoon/`
```
page.tsx                 # ① 각색 대시보드: 회차 목록 + "원작→컷 재구성" 시작
storyboard/page.tsx      # ② 비트/샷리스트 편집 (소설 씬에서 생성된 컷)
cast/page.tsx            # ③ 캐스트: 소설 캐릭터 → image character_id 등록
render/page.tsx          # ④ 렌더 콘솔 (SSE 진행률 그리드)
letter/page.tsx          # ⑤ 레터링: 드래그 말풍선 + 인플랫폼 미리보기 (GATE)
preview/page.tsx         # ⑥ 세로 스크롤 리더 + 익스포트
layout.tsx               # 웹툰 서브내비/공통 셸
```

### 컴포넌트 — `blog/src/components/novel/webtoon/`
```
BeatCard.tsx        # 컷 카드(shot/loc/char/대사) 인라인 편집
RenderGrid.tsx      # 70셀 그리드, SSE 구독 → 완료 즉시 썸네일
BubbleEditor.tsx    # 패널 위 말풍선 드래그/타입/한글 (오버레이)
WebtoonReader.tsx   # 인플랫폼 세로 스크롤 뷰어(패널 <img S3> + CSS 말풍선)
CastPanel.tsx       # 캐릭터→character_id 등록/레퍼런스
```

### API 라우트 — `blog/src/app/api/novels/[id]/webtoon/`
```
route.ts                 # 웹툰 회차 CRUD(메타/비트/렌더상태 저장)
beats/route.ts           # 소설 씬 → 비트 재구성 (gpuFetch novel/condense·scene/*·korean/*)
cast/route.ts            # 캐릭터 → character_id 등록 (gpuFetch image/character/create)
render/route.ts          # 70컷 일괄 제출 + 상태 폴링 → SSE (generate-image 패턴 확장)
qa/route.ts              # vision/describe 의도일치 검증
export/route.ts          # 자가완결 HTML 내보내기(buildViewer 이식)
```

### 공용 로직(이식) — `blog/src/lib/webtoon/`
```
genJobs.ts          # 비트 → image/generate 잡 합성 (gen_ep01full.py 이식)
buildViewer.ts      # 패널+lettering → HTML (build_viewer.py 이식, 익스포트용)
presets.ts          # 검증된 운영값(샷별 IP-Adapter·강화 negative·소품 프리셋)
types.ts            # Beat, Dialogue, Job, Lettering 타입
```

---

## 3. 데이터 흐름 (소설 → 웹툰)

```
소설(이미 시스템에 존재)
  chapters / scenes / characters / plots / analysis(emotion·pacing)
        │  ②beats/route.ts
        ▼  gpuFetch: novel/chapter/condense → 웹툰 분량 압축
           gpuFetch: novel/scene/{dialogue,description,transition} → 컷 단위 비트
           gpuFetch: korean/character-voice → 인물별 말투 입힘
           gpuFetch: novel/analyze/emotion_map·pacing → 강조/침묵·컷밀도
  Beat[]  (shot/loc/char/scene/dialogue[]/bubble_space)  ← 인라인 편집(②)
        │  ③cast: 소설 character → gpuFetch image/character/create → character_id
        │  lib/webtoon/genJobs.ts (샷→IP-Adapter, 강화 negative, bubble-space→pos)
        ▼
  Job[]   → ④render/route.ts (gpuFetch image/generate ×70 + status 폴링) ──SSE──▶ RenderGrid
        ▼  패널 = GPU가 Wasabi S3 업로드 → S3 key/url
  qa: gpuFetch vision/describe(패널) ↔ beat 의도 대조 → ⚠불일치 플래그
        ▼  ⑤lettering: BubbleEditor 드래그 (얼굴회피는 detect/image 보조)
  Lettering[]
        ▼  ⑥ WebtoonReader.tsx(인플랫폼) / buildViewer.ts(익스포트 HTML)
  완성 웹툰 회차
```

---

## 4. 렌더 파이프라인 — `generate-image` 패턴 확장

기존 `api/ai/generate-image/route.ts`가 이미 `image/generate`→`status` 폴링→SSE를 한다. 웹툰 렌더는:

1. `render/route.ts`에서 **70개 잡을 `genJobs.ts`로 합성**(각 잡에 `character_id`·`ip_adapter_mode`·`ip_adapter_strength`·강화 `negative_prompt`·`seed`·hq 파라미터 주입). ← 기존 generate-image는 단일/소수 + character_id 미전달이므로 **그 부분을 확장**.
2. 순차 제출(서버 1 GPU 순차 처리) — 각 잡 `job_id` 수집 후 `status` 폴링, 완료 시 S3 filename 확보.
3. **SSE로 셀 단위 진행**(대기 위치/렌더링/완료 썸네일·실패) → `RenderGrid`가 구독.
4. 실패/불만 셀만 **부분 재렌더**(프롬프트·시드 조정 후 재제출). 소품 인서트는 "객체강제 프리셋" 적용.

검증된 운영값(`presets.ts`로 이식):
- 샷별 IP-Adapter: `wide/full→{mode:full,strength:0.4}`, `close/emotion→{mode:face,strength:0.5}`, **≥0.6 금지**.
- animagine 강화 negative(가짜 말풍선/gibberish 제거 토큰) + 긍정 프롬프트 "speech bubble" 금지.
- 품질 프로파일 hq(steps30/cfg6.5/896×1280/품질토큰). 소품 인서트 객체강제 프리셋.

---

## 5. 뷰어 & 데이터 모델

- **인플랫폼 뷰어**: `WebtoonReader.tsx` = 세로 스크롤 컨테이너에 패널 `<img src={image-proxy?f=…}>` + `position:absolute` CSS 말풍선 div(type별 클래스). 소설 리더 UX 재사용. base64 임베드 불필요(플랫폼 내부라 S3 직참조).
- **익스포트**: `buildViewer.ts` = 검증된 자가완결 HTML(패널 base64 임베드) 생성 → 다운로드. 외부 공유/백업용.
- **데이터 저장(택1)**:
  - A(권장·소설과 동형): 웹툰 회차를 **GPU 서버에 저장**(novel `project_id`에 연결, story/chain 활용) — 일관 + 연속성 엔진 재사용.
  - B: blog **Prisma에 `Webtoon`/`WebtoonPanel` 모델 추가**(소셜·발행·메타), 패널은 S3 key. 커뮤니티 발행(좋아요/구독/북마크 기존 모델 재사용)까지 노린다면 B.
  - 패널 이미지는 어느 쪽이든 **Wasabi S3**(GPU `image/s3/*`)에 저장된 것을 URL 참조.

---

## 6. 마일스톤 (WeRUB CLI 작업 단위)

- **M1 — 탭 + 재구성**: NovelSubNav 탭 추가, `webtoon/page`+`storyboard`, `beats/route.ts`(소설 씬→비트), BeatCard 편집. 렌더 없이 "각색 초안"까지.
- **M2 — 렌더 콘솔**: `cast/route.ts`(character_id 등록) + `render/route.ts`(generate-image 확장, SSE) + RenderGrid + 부분 재렌더 + `qa`(vision).
- **M3 — 레터링·뷰어**: BubbleEditor 드래그 + WebtoonReader 인플랫폼 리더 + `export`(buildViewer).
- **M4 — 발행·연속성**: Prisma 모델(옵션 B) + 커뮤니티 발행, 시리즈/연속성(story/chain), 다국어(translate).

---

## 7. WeRUB CLI 착수 체크리스트

해당 repo에서 Claude Code 열고:

1. `blog/.env`에 `GPU_API_URL`(+키) 설정 확인 — `gpu-proxy.ts`가 읽음(이미 운용 중일 것).
2. 기존 패턴 정독: `lib/gpu-proxy.ts`, `api/ai/generate-image/route.ts`(SSE), `api/ai/novel/[...path]/route.ts`, `components/novel/NovelSubNav.tsx`.
3. 검증된 운영값/생성기/뷰어 로직은 이 하네스 repo의 **`examples/ep01_full/{gen_ep01full.py,build_viewer.py}`** 와 루트 `README.md`"검증된 렌더 운영값"을 TS로 이식 원본으로 사용.
4. M1부터: 탭 → `beats/route.ts`(gpuFetch novel/condense·scene) → BeatCard. 작동 확인 후 M2 렌더.
5. 렌더는 길다(70컷). 반드시 SSE + 부분 재렌더 + 실패 자동표시. `image/status` 큐 위치를 그대로 노출.

> 인증: 모든 웹툰 라우트는 소설과 동일하게 `getCurrentUser()`(next-auth) 가드. 프록시는 절대 GPU 키를 프론트로 노출하지 않음(서버 라우트에서만).
