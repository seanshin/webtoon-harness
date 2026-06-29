---
name: webtoon-assembly
description: "웹툰 조립·레터링·검수·패키징 방법론. 텍스트 없는 패널 PNG를 세로 스크롤 뷰어(index.html)로 잇고 letterer의 오버레이 스키마(ep{NN}_lettering.md)를 읽어 각 패널 위에 CSS 절대배치 한글 말풍선을 얹어 조립하고, letterer의 말풍선/레터링 오버레이 명세(대사·생각·외침·나레이션)를 설계하며, 웹툰 QA/검수(패널 수·레퍼런스 외형 일관성·배경 연속성·오버레이 한글 정확+말풍선 위치 적절·대사 흐름·반전 전달·손상/중복 이미지)와 회차 간 연속성 관리, 최종 패키징을 수행할 때 사용한다. episode-compositor·quality-reviewer·continuity-manager·showrunner와 letterer가 참조한다. 회차를 다시 조립·재조립·수정·보완하거나 재검수·업데이트할 때도 반드시 사용한다."
---

# 웹툰 조립·검수 방법론 (webtoon-assembly)

렌더가 끝난 패널을 "읽히는 웹툰"으로 만드는 마지막 공정이다. 조립(세로 스크롤 뷰어) → 레터링(말풍선) → QA/검수 → 연속성 관리 → 최종 패키징까지를 다룬다. 특정 회차에 맞추지 말고 어느 회차에든 적용되게 일반화해 쓴다. {NN} = 2자리 회차 번호.

핵심 원칙(왜 이렇게 하나):
- **순서가 서사다.** 패널은 panel_001 → panel_050+ 순서가 곧 독서 흐름이며 긴장 곡선·반전 타이밍이 여기에 실린다. 순서를 깨면 이야기가 깨진다.
- **모바일 세로 스크롤이 기본 매체다.** 독자는 손가락으로 내려 읽는다. 데스크톱도 중앙 정렬된 모바일 폭으로 본다.
- **가독성이 작화를 이긴다.** 말풍선이 얼굴/핵심 작화를 가리면 독자는 이탈한다. 대사 위주 웹툰일수록 더 그렇다.
- **검수는 증명이다.** "좋아 보인다"가 아니라 측정값과 교차 비교로 합격을 증명한다.

---

## 1. 세로 스크롤 뷰어 조립법 (episode-compositor)

왜: 패널을 한 줄기 세로 스트립으로 이어, 손가락 스크롤만으로 끊김 없이 읽게 만든다.

**이 하네스의 말풍선은 HTML/CSS 오버레이다.** 패널 PNG에는 **텍스트가 없고**(로컬 디퓨전은 한글을 못 그려 작화만 렌더), 한글 대사는 조립 단계에서 letterer의 `ep{NN}_lettering.md` 오버레이 스키마를 읽어 **각 패널 위에 CSS 절대배치 말풍선 div로 얹는다**. 따라서 조립은 (a) 텍스트 없는 패널을 순서대로 세로로 잇고, (b) 그 위에 한글 말풍선을 절대배치하는 두 겹 공정이다. 한글은 오버레이라 100% 정확하고 자유롭게 수정된다(이미지 베이크 깨짐 문제 소멸).

골격은 참조 뷰어 패턴(고정폭 `.viewer` 컨테이너 → `.panel { position: relative }` → `.bubble { position: absolute }`)을 따른다. 외부 의존성 없는 단일 HTML이라 어디서든 열어 검수할 수 있다. 처음부터 새로 짜지 말고 패널 목록과 말풍선 데이터만 채운다.

### 절차
1. `_workspace/05_panels/ep{NN}/`의 PNG를 파일명 오름차순(panel_001 → …)으로 수집한다(panel-validator 통과본, **텍스트 없는 아트**).
2. `_workspace/04_visual/ep{NN}_lettering.md`(letterer 오버레이 스키마)를 Read해 패널별 `bubbles`(speaker/type/text_ko/pos/tail/max_width)를 읽는다. 무대사 패널은 `bubbles: []`.
3. 패널마다 `position:relative`로 감싼 컨테이너 안에 `<img>`(원본 비율, 폭 100%·높이 auto)를 깔고, 그 위에 lettering.md의 각 말풍선을 `position:absolute` div로 얹는다:
   ```html
   <div class="panel">
     <img src="../../05_panels/ep{NN}/panel_001.png" alt="panel 001">
     <div class="bubble tail-bl" style="top:6%; left:6%; max-width:58%;">여기가… 맞나?</div>
   </div>
   ```
   - `img src`는 결과 파일(`06_assembly/ep{NN}/index.html`) 기준 상대경로(`../../05_panels/...`). 또는 패널을 동일 폴더로 복사해 참조해도 된다.
   - 말풍선 좌표는 lettering.md의 `pos`(패널 박스 좌상단 기준 %)를 `top/left`(또는 `right/bottom`)에 그대로 옮긴다. `type`별 클래스(speech/thought/shout/narration/sfx), `tail` 방향, `max_width`도 반영한다(§5 art-director 비주얼 토큰).
   - 패널 간 간격은 `0`=무봉제(연속 컷), 양수=장면 전환/시간 경과/침묵 컷("쿵"). lettering.md의 리듬 힌트와 샷리스트 SCENE BREAK를 근거로 정한다.
4. 브라우저로 열어 스크롤·이음새·말풍선 가독을 육안 확인한다. **말풍선이 인물 얼굴/핵심 작화를 가리면** lettering.md의 `pos`를 여백 쪽으로 조정하고, 패널 자체에 여백이 없어 어디 놓아도 가려지면 **letterer/panel-validator에 피드백**한다(letterer는 위치 재지정, panel-validator는 오버레이 공간 확보 재렌더).

### 구조·스타일 규칙 (참조 뷰어 패턴)
- **반응형 폭(모바일 우선)**: `.viewer { width: 720px; max-width: 100% }` 중앙 정렬. 패널 폭은 100%로 채우고 높이는 auto.
- **패널 상대배치 + 말풍선 절대배치**: `.panel { position: relative; line-height: 0 }`로 감싸고 `.bubble { position: absolute }`로 얹는다. 좌표는 % 기준이라 폭이 바뀌어도 말풍선이 패널을 따라간다.
- **패널 간 이음새**: 간격을 `0`=무봉제 연결(한 장면의 연속 컷), 양수=칸 분리(장면 전환·시간 경과). 의미에 맞게 쓴다.
- **lazy-load**: `<img loading="lazy" decoding="async">`. 50+ 패널 회차의 초기 로딩·메모리 부담을 줄인다.
- **결손 표시**: 이미지 로드 실패 시 칸을 비우지 않고 경고 플레이스홀더를 보여준다(`img.onerror`). 누락을 숨기지 않아야 검수가 잡는다.
- **데이터/표현 분리**: 패널·말풍선은 데이터(패널 목록 + lettering.md), 스타일은 CSS. 재조립·수정 시 데이터만 갈아끼운다.

### 결손·순서 처리
- 번호가 비면(panel_007 없음) 당겨 붙이지 말고 그 자리에 결손을 표시하고 panel-artist에 재렌더를 요청한다. 순서가 어긋나면 반전 타이밍이 무너진다.
- 0바이트/손상 PNG도 결손으로 취급한다.

---

## 2. 레터링 섹션 (letterer → episode-compositor 오버레이용)

왜: 대사 위주 고긴장 웹툰에서 말풍선은 정보·감정·반전을 나르는 주된 통로다. 잘못 놓으면 작화가 좋아도 안 읽힌다. **이 하네스에서 말풍선은 패널 위에 HTML/CSS로 얹는 오버레이다(in-image 베이크 폐지)**. letterer는 이 섹션 규칙으로 `ep{NN}_lettering.md`(오버레이 스키마)를 설계하고, **episode-compositor가 이를 읽어 CSS 절대배치 말풍선으로 조립**하며, panel-validator는 패널에 **말풍선이 들어갈 여백/저복잡도 공간**이 확보됐는지(얼굴·핵심 작화 회피)를 본다. 한글은 오버레이라 100% 정확하고 자유롭게 수정되므로 letterer는 위치·리듬·분량에 집중한다.

### 말풍선 종류 (template의 `type`)
- **dialogue(대사)**: 입 밖으로 낸 말. 흰 배경·검은 테두리·둥근 모서리, 꼬리(`tail`)가 화자를 가리킨다.
- **thought(생각)**: 속마음. 점선 테두리·기울임. 꼬리 없음(또는 구름 점).
- **shout(외침)**: 비명·고함·충격. 두꺼운 테두리·굵은 글씨·약간의 기울기. 반전·클라이맥스 패널에서 강하게.
- **narration(나레이션)**: 화자 밖 서술·시간/장소 캡션. 사각 박스, 꼬리 없음. **남발 금지** — 내레이션 최소화가 원칙이며, 대사로 전할 수 있으면 대사로 전환한다.

### 위치 규칙
- **읽기 순서**: 한 패널 안에서 위→아래, 좌→우 순으로 자연히 읽히게 배치한다. 먼저 말하는 풍선이 위/왼쪽.
- **얼굴·핵심 작화 회피**: 인물 표정과 반전 단서를 가리지 않는다. 여백(하늘·바닥·배경)에 놓는다.
- **꼬리 방향(tail)**: 꼬리는 화자 입/머리 쪽을 가리킨다(`left/right/up/down`). 화자 귀속이 한눈에 보여야 한다.
- **가장자리 안전 여백**: 말풍선이 패널 밖으로 잘리지 않게 x/y를 5~95% 안에 둔다.

### 가독성 원칙 (대사 위주 웹툰)
- **폰트 크기**: 본문 대사는 충분히 크게(`--bubble-fs` 기준 16~18px급). 모바일 화면에서 작으면 곧 이탈.
- **대비**: 글자색과 풍선 배경의 대비를 확실히(검정 글자/흰 풍선, 나레이션은 흰 글자/어두운 박스).
- **한 풍선의 분량**: 호흡 단위로 끊는다. 긴 대사는 여러 풍선으로 분할해 긴장의 리듬을 만든다.
- **줄바꿈**: `word-break: keep-all`로 한국어 어절이 어색하게 끊기지 않게 한다.
- **레터링 방식**: 이 하네스의 기본은 **HTML/CSS 오버레이**(텍스트 없는 패널 위에 조립 단계에서 말풍선을 얹음). letterer는 오버레이 스키마를 쓰고 episode-compositor가 CSS 절대배치로 렌더한다. 이미지에는 글자를 굽지 않는다(로컬 디퓨전은 한글을 못 그림).
- **위치 정밀도(오버레이의 핵심 리스크)**: 한글 정확성은 오버레이가 보장하므로 깨짐 걱정은 없다. 대신 말풍선이 **인물 얼굴·핵심 작화를 가리지 않도록** `pos`(패널 좌상단 기준 %)를 여백 쪽으로 잡는다. 그래서 (a) 말풍선당 대사를 짧게 끊고(가독·리듬), (b) 패널의 빈 공간 위치를 보고 `pos`를 지정하며, (c) 가릴 공간밖에 없으면 letterer/panel-validator 피드백으로 위치 재지정·여백 확보 재렌더를 받는다.

### `ep{NN}_lettering.md` 형식 (letterer 출력 → episode-compositor 오버레이, 계약 §3·§5 스키마)
```yaml
### panel_001
- bubbles:
  - speaker: 지호
    type: speech | thought | shout | narration | sfx
    text_ko: "여기가… 맞나?"
    pos: { x: "6%", y: "6%" }        # 패널 박스 좌상단 기준 %
    tail: bottom-left | bottom-right | none
    max_width: "58%"
### panel_004
- bubbles: []                        # 무대사 침묵 컷(말풍선 없음)
```
- `text_ko`는 대본 원문 그대로(맞춤법·문장부호 포함) — episode-compositor가 그대로 div에 넣고 오버레이라 100% 정확하다.
- `pos`는 패널 박스 좌상단 기준 %(`x`/`y`) → compositor가 `top`/`left`(또는 `right`/`bottom`)로 옮긴다. 얼굴·핵심 작화를 피한 여백을 가리킨다.
- `type`은 말풍선 스타일 클래스(speech/thought/shout/narration/sfx, §5 art-director 비주얼 토큰), `tail`은 꼬리 방향, `max_width`는 풍선 최대 폭.

---

## 3. QA 체크리스트 (quality-reviewer)

왜: 결함은 일찍·객관적으로 잡을수록 재작업이 싸다. 셀 수 있는 것은 스크립트로 측정하고, 의미는 교차 비교로 검증한다. **점진적 QA** — 모듈이 완성되는 즉시 검증한다.

**2단 검증 분업**: 패널 단위 1차 검증(캐릭터/배경/한글/프롬프트 충실도)은 비주얼팀 **panel-validator**가 렌더 중 생성-검증 루프로 거른다(`ep{NN}_validation.md`). quality-reviewer는 그 뒤 **조립된 회차 전체**를 검수하는 끝단 게이트로, validation.md의 ACCEPT-FLAG 패널을 먼저 파악하고 회차 흐름·반전·연속성·플래그 패널의 최종 수용에 집중한다.

### 검수 항목과 PASS/FIX/REDO 기준
| 항목 | 측정/판단 | PASS | FIX | REDO |
|------|-----------|------|-----|------|
| 패널 수 50+ | PNG 개수 카운트 | ≥50 | — | <50(비트 분할 재작업) |
| 손상/0바이트/중복 | 바이트·PNG 헤더·**md5 중복** | 모두 정상·고유 | 소수→재렌더 | 다수 손상/중복 |
| 외형 일관성 | **refs/ 레퍼런스 대조**·육안 | 유지 | 1~2칸 경미 | 인물 식별 깨짐 |
| 배경/장소 연속성 | scene_id↔location 대조 | 씬 내 일관 | 1~2칸 보정 | 씬 중 배경 급변 다발 |
| 오버레이 한글·말풍선 위치 | 오버레이 텍스트↔대본 대조 + 말풍선이 얼굴/작화 가림 점검 | 한글 정확·말풍선이 핵심 작화 안 가림 | 소수 위치 조정 | 대거 가림·읽기순서 붕괴 |
| 대사 흐름 | 인접 패널 이어 읽기 | 자연스러움 | 국소 손질 | 흐름 단절 |
| 반전 전달 | 대본↔패널↔오버레이 대사 교차 | 드러남 | 단서 보강 | 반전 미전달 |
| 긴장 곡선 | 흐름·클리프행어 | 우상향+훅 | 늘어짐 손질 | 곡선 붕괴 |

- **PASS**: 그대로 통과. **FIX**: 국소 수정으로 해결(재렌더 불필요하거나 경미). **REDO**: 재렌더/재집필이 필요한 근본 결함. 등급을 흐리면 재작업 루프가 비효율이 된다.

### 객관 지표 측정 (스크립트로)
- 패널 수: `_workspace/05_panels/ep{NN}/`의 `panel_*.png` 개수를 센다.
- 0바이트: 파일 크기 0인 PNG를 찾는다.
- 손상: PNG 매직 바이트(`\x89PNG`)로 헤더를 확인한다.
- **md5 중복**: `md5 -r panel_*.png | awk '{print $1}' | sort | uniq -d` — 비어야 정상(서로 다른 패널이 같은 이미지면 사고). EP01에서 실제 발생했으므로 필수. (참조: `references/qa-checks.md`)

### 경계면 교차 검증 (최우선)
가장 비싼 실패는 **단절**이다: 대본(`03_episode/ep{NN}_script_final.md`)·반전 설계(`02_story/twist-plan.md`)엔 반전이 있는데 실제 패널/레터링엔 안 드러나는 경우. 항상 대본 ↔ 레터링 ↔ 패널을 교차로 본다 — 반전이 시각/대사로 표현됐는지, 복선이 앞 패널에 심겼는지.

### 수정 지시 작성
대상·문제·조치·담당을 명시한다. 예: "panel_023 말풍선이 화자 얼굴을 가림 → 우상단 여백 이동 (담당: letterer/episode-compositor)". 모호어("어색함") 금지.

### 재작업 루프
FIX/REDO는 담당 에이전트(배치→episode-compositor, 작화/외형/손상→panel-artist, 말풍선→letterer, 반전/대사→script-editor·twist-master)에게 보낸다. 루프는 **최대 2회**, 이후에도 REDO면 showrunner에 에스컬레이션.

---

## 4. 연속성 관리 (continuity-manager)

왜: 회차가 쌓이면 외형·설정·떡밥이 어긋나기 쉽다. 단일 원장에 누적해야 다음 회차가 모순 없이 이어진다. `continuity.md`는 **덮어쓰지 말고 회차별로 이어 쓴다**(과거 상태를 알아야 모순을 잡는다).

추적할 원장:
- **캐릭터 외형 원장**: 인물별 고정 특징(머리색/의상/체형/식별점) + 회차별 변경 이력("ep03에서 X→Y").
- **설정·세계관 원장**: 능력 규칙·지명·조직·시간선의 추가/변경.
- **플롯·관계·정보 상태**: 회차 종료 시점 스냅샷, 누가 무엇을 아는지(정보 비대칭).
- **반전 떡밥 원장(표)**: 복선 / 심은 회차 / 회수 예정 / 회수 여부 / 비고. **미회수 떡밥을 항상 표면에** 둔다 — 심은 복선은 회수 의무가 있다.
- **다음 회차 주의사항**: 일관성·회수 관점 체크리스트(명령형).

정본은 `02_story/*`(characters/world/series-arc/twist-plan)와 `04_visual/*` 시트다. 산출물이 정본과 충돌하면 산출물이 틀린 것으로 보거나 정본 갱신을 요청한다(임의 판단 금지, 양쪽 기록).

---

## 5. 최종 패키징 (showrunner)

왜: 합격본은 그 자체로 열어보고 배포할 수 있어야 한다. RELEASE는 무엇이 포함됐는지(매니페스트)와 합격 근거, 다음 회차 시드를 함께 담는다.

사인오프 기준: `qa_report.md`(회차 내 품질)와 `continuity.md`(회차 간 연속성)를 **동시에** 만족해야 한다. REDO나 미해결 모순이 있으면 사인오프하지 않고 되돌린다.

`_workspace/RELEASE/ep{NN}/` 구조:
```
RELEASE/ep{NN}/
  index.html          # 뷰어(상대경로가 깨지지 않게 panels/ 동봉 권장)
  panels/             # 패널 PNG 사본(또는 안정적 참조)
  qa_report.md        # 품질 합격 근거
  RELEASE_NOTES.md    # 사인오프 판정 · 포함 목록 · 다음 회차 시드
```
- **다음 회차 시드**: 이번 클리프행어와 미회수 떡밥을 이어받아 다음 회차 시작점을 continuity-manager와 합의해 `RELEASE_NOTES.md`에 적고, 시나리오팀(series-plotter·twist-master)에 넘긴다.

---

## 6. 출력 경로 (§3 데이터 흐름 준수)

- 조립 뷰어: `_workspace/06_assembly/ep{NN}/index.html` (episode-compositor)
- 검수 보고: `_workspace/06_assembly/ep{NN}/qa_report.md` (quality-reviewer)
- 연속성 기록: `_workspace/06_assembly/continuity.md` (continuity-manager, 누적)
- 최종 패키지: `_workspace/RELEASE/ep{NN}/` (showrunner)

입력 경로: 패널 `_workspace/05_panels/ep{NN}/panel_*.png`, 레터링 `_workspace/04_visual/ep{NN}_lettering.md`, 확정 대본 `_workspace/03_episode/ep{NN}_script_final.md`, 반전 설계 `_workspace/02_story/twist-plan.md`, 정본 `_workspace/02_story/*`·`_workspace/04_visual/*`.

## 7. 후속 작업(다시/재조립/수정/보완)
- 산출물이 이미 있으면 통째로 새로 만들지 말고 변경분만 교체한다. 합격한 부분은 보존한다.
- 재조립: 변경된 패널/말풍선의 데이터 항목만 교체. 재검수: 재작업된 항목만 재검증해 판정 갱신. 연속성: 변한 항목만 이어 기록.
- 자산: 동작하는 뷰어 골격은 `assets/viewer-template.html`. 바로 쓰는 검증 명령은 `references/qa-checks.md`.
