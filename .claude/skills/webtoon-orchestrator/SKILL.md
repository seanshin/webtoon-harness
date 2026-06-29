---
name: webtoon-orchestrator
description: "웹툰 제작 에이전트 팀(27명)을 조율하는 메인 오케스트레이터. 인기 웹툰 트렌드 조사 → 대사 위주·고긴장·매 회차 반전 시나리오 작성 → 캐릭터 다각도 레퍼런스 시트를 먼저 렌더해 character_id로 등록 → 회차당 50+ 패널을 로컬 GPU 서버(WeRU.B 이미지 API) 큐로 텍스트 없는 아트만 배치 렌더(character_id IP-Adapter 일관성) → panel-validator 생성-검증 루프로 기준 만족까지 재생성 → 한글 말풍선 HTML 오버레이로 세로 스크롤 뷰어 조립까지 전 과정을 단계별 팀 재구성으로 운영한다. 트리거: '웹툰 만들어/제작', '웹툰 한 화/회차 만들어', '웹툰 시나리오부터 이미지까지', '웹툰 에피소드 제작', '웹툰 하네스 실행'. 후속 작업: '다음 화 만들어', '이 회차 다시/수정/보완', '반전 더 강하게', '패널 다시 그려', '특정 단계만 다시 실행', '이전 결과 기반 개선' 등에도 반드시 이 스킬을 사용. 단순 웹툰 추천/감상은 직접 응답."
---

# Webtoon Orchestrator — 웹툰 제작 팀 조율

웹툰 한 회차를 트렌드 조사부터 완성 뷰어까지 만들어내는 통합 오케스트레이터. 27개 전문 에이전트를 **4개 단계별 팀**으로 순차 운영한다.

## 실행 모드: 에이전트 팀 (단계별 재구성)

세션당 활성 팀은 1개뿐이므로, 각 Phase마다 `TeamCreate`로 팀을 만들고 작업이 끝나면 `TeamDelete`로 정리한 뒤 다음 Phase 팀을 만든다. 이전 팀의 산출물은 `_workspace/`에 남아 다음 팀이 Read로 이어받는다. 모든 팀원 스폰과 Agent 호출에 **`model: "opus"`**를 명시한다.

## 에이전트 구성 (27명, 4팀)

| 팀 | 팀원 | 역할 | 스킬 | 주요 출력 |
|----|------|------|------|----------|
| **리서치팀** | trend-scout | 장르/트로프 동향 | webtoon-trend-research | 01_research/trend-scout.md |
| | platform-ranker | 플랫폼 랭킹·연재구조 | webtoon-trend-research | 01_research/platform-ranker.md |
| | audience-analyst | 독자층·이탈·몰입 | webtoon-trend-research | 01_research/audience-analyst.md |
| | hook-analyst | 후킹/반전 메커니즘 역설계 | webtoon-trend-research | 01_research/hook-analyst.md |
| | trend-synthesizer | 종합 기획 브리프 | webtoon-trend-research | 01_research/trend-brief.md |
| **시나리오팀** | concept-architect | 하이콘셉트/로그라인 | webtoon-scenario | 02_story/concept.md |
| | worldbuilder | 세계관·규칙 | webtoon-scenario | 02_story/world.md |
| | character-designer | 캐스트(외형+성격+아크) | webtoon-scenario | 02_story/characters.md |
| | series-plotter | 시리즈 아크·회차 맵 | webtoon-scenario | 02_story/series-arc.md |
| | twist-master | 매 회차 반전 설계 | webtoon-scenario | 02_story/twist-plan.md |
| | tension-engineer | 긴장 곡선·클리프행어 | webtoon-scenario | 02_story/tension-curve.md |
| | episode-outliner | 회차 비트시트(50+ 패널) | webtoon-scenario | 03_episode/ep{NN}_beatsheet.md |
| | dialogue-writer | 대사 위주 대본 | webtoon-scenario | 03_episode/ep{NN}_script.md |
| | script-editor | 교정·반전 명료성 | webtoon-scenario | 03_episode/ep{NN}_script_final.md |
| **비주얼팀** | art-director | 스타일 바이블·일관성 토큰·장소 토큰·말풍선 규약 | webtoon-panel-breakdown | 04_visual/style-bible.md, character-sheets.md |
| | ref-sheet-artist | 캐릭터 다각도/표정 레퍼런스 시트(패널 전 선행) | webtoon-panel-render | 04_visual/refs/*.png, refs/INDEX.md |
| | panel-director | 50+ 패널 샷리스트(scene_id/location) | webtoon-panel-breakdown | 04_visual/ep{NN}_shotlist.md |
| | letterer | 한글 말풍선 오버레이 명세(좌표·type·max_width) | webtoon-assembly | 04_visual/ep{NN}_lettering.md |
| | prompt-smith | 패널별 영문 아트 프롬프트 + jobs.json(character_id·IP-Adapter·장소토큰, 텍스트 없음) | webtoon-panel-render | 04_visual/ep{NN}_prompts.md, ep{NN}_jobs.json |
| | panel-artist-a | scene 그룹 A 렌더 | webtoon-panel-render | 05_panels/ep{NN}/panel_*.png |
| | panel-artist-b | scene 그룹 B 렌더 | webtoon-panel-render | 05_panels/ep{NN}/panel_*.png |
| | panel-artist-c | scene 그룹 C 렌더 | webtoon-panel-render | 05_panels/ep{NN}/panel_*.png |
| | panel-validator | 패널 6축 검증·재생성 루프 게이트(general-purpose) | webtoon-panel-render | 04_visual/ep{NN}_validation.md |
| **조립검수팀** | episode-compositor | 세로 스크롤 뷰어 조립 + 한글 말풍선 CSS 오버레이 | webtoon-assembly | 06_assembly/ep{NN}/index.html |
| | quality-reviewer | QA 검수(general-purpose) | webtoon-assembly | 06_assembly/ep{NN}/qa_report.md |
| | continuity-manager | 회차 간 연속성 | webtoon-assembly | 06_assembly/continuity.md |
| | showrunner | 총괄·사인오프·패키징 | webtoon-assembly | RELEASE/ep{NN}/ |

## 워크플로우

### Phase 0: 컨텍스트 확인 (후속 작업 판별)

`_workspace/` 존재 여부와 사용자 요청으로 실행 모드를 정한다.

1. `_workspace/` 미존재 → **초기 실행**. Phase 1로.
2. `_workspace/` 존재 + "다음 화" 요청 → **새 회차 실행**. {NN}을 증가시키고, 02_story·style-bible·character-sheets·**refs/(레퍼런스 시트)**·continuity.md는 재사용(Read, 재렌더 금지 — 시리즈 일관성), 03_episode 이후만 새로 생성.
3. `_workspace/` 존재 + "이 회차의 OO만 다시" 요청 → **부분 재실행**. 해당 단계 팀만 재구성하여 호출하고, 그 산출물만 덮어쓴다. 하위 단계(예: 대본 수정 시 샷리스트→렌더→조립)는 영향받는 만큼만 재실행.
4. `_workspace/` 존재 + 새 기획 입력 → **새 기획 실행**. 기존 `_workspace/`를 `_workspace_{YYYYMMDD_HHMMSS}/`로 이동 후 Phase 1.

부분/새회차 재실행 시 이전 산출물 경로를 팀원 프롬프트에 포함해 "Read 후 개선점만 반영"을 지시한다.

### Phase 1: 준비

1. 사용자 입력 분석 — 회차 번호 {NN}, 장르 방향(있으면), 제약(수위·길이·톤).
2. `_workspace/00_input/brief.md`에 입력·회차 번호·제약을 기록.
3. 작업 디렉토리 보장: `mkdir -p _workspace/{00_input,01_research,02_story,03_episode,04_visual,05_panels,06_assembly,RELEASE}`.

### Phase 2: 트렌드 리서치 (리서치팀)

**실행 모드:** 에이전트 팀

1. `TeamCreate(team_name: "webtoon-research", members: [trend-scout, platform-ranker, audience-analyst, hook-analyst, trend-synthesizer])` — 전원 `agent_type`=커스텀 이름, `model: "opus"`.
2. `TaskCreate`로 5개 작업 등록. trend-synthesizer 작업은 나머지 4개에 `depends_on`.
3. 4명의 조사자가 병렬 조사, 흥미로운 발견을 SendMessage로 공유(hook-analyst↔trend-scout 등).
4. trend-synthesizer가 4개 산출물을 종합 → `01_research/trend-brief.md`.
5. `TeamDelete`로 정리. (산출물은 `_workspace/`에 보존)

### Phase 3: 시나리오 (시나리오팀)

**실행 모드:** 에이전트 팀 (파이프라인 + 팬아웃)

1. `TeamCreate(team_name: "webtoon-story", members: [concept-architect, worldbuilder, character-designer, series-plotter, twist-master, tension-engineer, episode-outliner, dialogue-writer, script-editor])`.
2. 작업 의존성: concept → world → characters(순차 조율) → series-arc → {twist-plan, tension-curve}(상호 조율) → beatsheet → script → script_final.
3. **매 회차 반전 보장**: twist-master가 twist-plan에 회차별 반전을 명시하고, script-editor가 script_final에서 반전이 명료하게 전달되는지 검수.
4. **50+ 패널 분량 확보**: episode-outliner가 비트를 충분히 쪼개 50패널 이상 분량을 만든다.
5. 산출물: `02_story/*`, `03_episode/ep{NN}_script_final.md`.
6. `TeamDelete`로 정리.

### Phase 4: 비주얼 프로덕션 (비주얼팀)

**실행 모드:** 에이전트 팀 (감독자 + 생성-검증 루프). **로컬 GPU 서버 큐 배치 렌더(weru_imagegen.py).**

**사전 점검(회차당 1회):** 렌더 시작 전 로컬 서버 도달성을 확인한다.
```bash
ssh -p 32200 weruby@121.161.70.94 "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8585/api/image/models"
# 200 이면 정상. 아니면 사용자에게 서버/SSH 상태 확인을 요청하고 렌더를 시작하지 않는다.
```

1. `TeamCreate(team_name: "webtoon-visual", members: [art-director, ref-sheet-artist, panel-director, letterer, prompt-smith, panel-artist-a, panel-artist-b, panel-artist-c, panel-validator])`.
2. **아트 디렉션**: art-director가 `style-bible.md`(작화·**장소 토큰 LOC_***·**말풍선 오버레이 규약**[폰트·type별 스타일] 포함) + `character-sheets.md`(일관성 토큰+레퍼런스 사양)를 만들고 팀에 공유.
3. **레퍼런스 시트 먼저(일관성 SSOT) + character_id 등록**: ref-sheet-artist가 주요 캐릭터의 대표 레퍼런스를 `weru_imagegen.py`로 렌더한 뒤 **`register`로 등록해 `character_id`(UUID)를 확정** → `04_visual/refs/`에 자산 저장 → `refs/INDEX.md`(캐릭터별 character_id+경로+외형)를 prompt-smith·panel-validator에 인계. **패널 렌더는 character_id 확정 후 시작.** (후속 회차는 기존 refs/INDEX.md의 character_id 재사용, 재등록 금지.)
4. **콘티+레터링 병렬**: panel-director가 `ep{NN}_shotlist.md`(50+ 패널, 각 패널 scene_id/location + **shot 필드**[wide|full|action→full/0.4, close|emotion→face/0.5] + 말풍선 여백 위치 힌트), letterer가 `ep{NN}_lettering.md`(**한글 말풍선 오버레이 스키마**: speaker/type/text_ko/pos/tail/max_width, 한글 짧게)를 병렬 작성.
5. **프롬프트 합성**: prompt-smith가 [영문 아트 프롬프트=스타일+장소토큰+character_id 앵커+구도/상태색+**말풍선 자리 비움, 텍스트 없음**]을 합성한 `ep{NN}_prompts.md`와 함께 `ep{NN}_jobs.json`(weru_imagegen.py gen 입력: output/prompt/model/style/negative_prompt/character_id/ip_adapter_mode·strength/width/height/seed)을 만들고 scene 그룹 A/B/C로 분배. **negative에 `text, speech bubble, caption, watermark` 필수**(한글은 오버레이가 얹으므로 이미지에 굽지 않는다). shot 필드로 IP-Adapter mode/strength 주입, **strength ≥ 0.6 금지**.
6. **렌더링 (큐 배치)**: 서버는 큐 기반(최대 1만 건, VRAM 경합 없이 순차 처리)이라 동시 세션 한도가 없다. panel-artist a/b/c가 자기 담당 scene 그룹의 jobs.json을 **한 번에 큐에 넣어** 렌더한다.
   ```bash
   python3 .claude/skills/webtoon-panel-render/scripts/weru_imagegen.py \
     gen --jobs <그룹 jobs.json> --out-dir _workspace/05_panels/ep{NN}
   ```
   헬퍼가 잡을 큐 등록 → 완료 백오프 폴링(429 자동 대기) → PNG 다운로드. 50패널 ≈ dreamshaper ~6s/장 5~6분.
7. **검증-재생성 루프 (핵심 — 기준 만족까지)**: 배치 렌더 직후 panel-validator가 6축(C1 캐릭터/character_id, C2 배경·장소 연속성, **C3 텍스트 없음+오버레이 공간**[굽힌 글자·말풍선이 없어야 하고 letterer 지정 위치에 가릴 것 없는 여백 확보], C4 프롬프트 충실도[구도 붕괴=strength 과다→0.4~0.5로 낮춰 재렌더], C5 장면 흐름, C6 무결성·md5중복) 검증 → ACCEPT/REGEN 판정. REGEN 패널은 prompt-smith가 잡 보강(시드 변경) → 담당 panel-artist가 그 패널만 재렌더 → 재검증. **패널당 최대 3회**, 초과 시 ACCEPT-FLAG(통과+한계 기록). 전 패널 통과 시 `04_visual/ep{NN}_validation.md`(각 패널 오버레이 가용 공간 메모 포함) 완성.
8. 산출물: `04_visual/*`(style-bible/character-sheets/refs+INDEX/shotlist/lettering/prompts/jobs.json/validation), `05_panels/ep{NN}/panel_*.png`(**텍스트 없는 검증 통과 아트**).
9. `TeamDelete`로 정리.

### Phase 5: 조립 · 검수 (조립검수팀)

**실행 모드:** 에이전트 팀 (생성-검증)

1. `TeamCreate(team_name: "webtoon-assembly", members: [episode-compositor, quality-reviewer, continuity-manager, showrunner])`.
2. episode-compositor가 **텍스트 없는** 패널 PNG를 세로 스크롤 `index.html`로 조립하고, letterer의 `ep{NN}_lettering.md` 오버레이 스키마를 읽어 각 패널 위에 **한글 말풍선 CSS 오버레이**(각 패널 `position:relative` 래퍼 + 말풍선 `position:absolute`, pos/max_width/tail/type별 스타일은 art-director 말풍선 오버레이 규약을 따름)를 얹는다. 한글은 100% 정확·수정 자유.
3. quality-reviewer가 점진적 QA — panel-validator의 `validation.md`(ACCEPT-FLAG 파악)를 먼저 읽고, 회차 전체로 패널 수 50+, **캐릭터 외형 일관성(character_id)**, **배경 연속성**, **오버레이 한글 대사 정확/가독·말풍선이 얼굴/핵심 작화를 가리지 않음**, **대사 흐름**, **반전 전달**, 손상/중복 이미지를 검수. PASS/FIX/REDO 판정.
4. FIX/REDO 패널 → panel-validator 루프 재투입(prompt-smith 보강+panel-artist 재렌더) 또는 SendMessage 피드백으로 해당 패널만 재작업(최대 2회 루프). 말풍선 위치/대사 문제는 letterer가 오버레이 스키마만 고치면 재렌더 없이 해결. 반전이 안 드러나면 시나리오팀/레터러로 피드백.
5. continuity-manager가 `continuity.md`를 갱신(회차 간 외형/설정/떡밥).
6. showrunner가 사인오프 후 `RELEASE/ep{NN}/`에 최종 패키징 + 다음 회차 시드(클리프행어 이어받기) 제안.
7. `TeamDelete`로 정리.

### Phase 6: 마무리

1. `_workspace/` 전체 보존(중간 산출물 = 감사 추적).
2. 사용자에게 결과 요약: 회차 제목·로그라인·반전 한 줄·패널 수·뷰어 경로(`RELEASE/ep{NN}/index.html`)·다음 회차 시드.
3. 피드백 요청: "반전 강도/대사 톤/작화 일관성에서 고치고 싶은 부분이 있나요?" (Phase 7 진화 연결)

## 데이터 흐름

```
trend-brief.md
   └→ concept → world → characters → series-arc → {twist-plan, tension-curve}
                                                       └→ beatsheet → script → script_final
script_final + characters
   └→ style-bible(+장소토큰 LOC_*, 말풍선 오버레이 규약)/character-sheets
        └→ refs/*.png (레퍼런스 시트, 패널 전 선행) → character_id 등록(register, refs/INDEX.md)
        └→ shotlist(scene_id/location/shot) + lettering(한글 말풍선 오버레이 스키마)
              └→ prompts(영문 아트 + character_id·IP-Adapter·장소토큰, 텍스트 없음) → jobs.json(텍스트 없는 아트, scene A/B/C)
                    └→ panel_*.png(텍스트 없음) ⇄ panel-validator 6축 검증-재생성 루프 ⇄ prompt-smith/panel-artist
                          └→ validation.md (전 패널 통과)
panel_*.png(텍스트 없음) + lettering.md → index.html(한글 말풍선 CSS 오버레이) → qa_report → (재작업 루프) → RELEASE/ep{NN}/
```

## 에러 핸들링

| 상황 | 전략 |
|------|------|
| 팀원 1명 실패/중지 | 리더가 유휴 알림 감지 → SendMessage 상태 확인 → 재시작 또는 대체 팀원 생성 |
| 팀원 과반 실패 | 사용자에게 알리고 진행 여부 확인 |
| 서버 큐 잡 실패/0바이트/손상 | 헬퍼 stderr의 실패 잡 목록으로 해당 잡만 재렌더(배치 전체 금지). 2회 실패 시 경고 후 통과, 보고서 명시 |
| 패널 md5 중복(서로 다른 패널이 동일 이미지) | 중복 패널 삭제 후 시드 바꿔 단독 재렌더. 크기/헤더 검사로는 못 잡으니 md5 검사 필수(EP01 실제 발생) |
| 배경 급변(도로→실내 등) | panel-validator C2 REGEN → prompt-smith가 장소 토큰(LOC_*) 강화 후 그 패널만 재렌더 |
| 구도 붕괴(정면 상반신으로 수렴) | strength 과다 신호 → ip_adapter_strength를 0.4~0.5로 낮추고 shot 재명시 후 그 패널만 재렌더(strength ≥ 0.6 금지) |
| 이미지에 글자 새어나옴 | panel-validator C3 REGEN → negative(`text, speech bubble, ...`) 강화 후 재렌더. (한글 대사 자체는 오버레이가 보장하므로 깨질 일 없음 — 깨진 한글은 잘못 베이크된 신호) |
| 캐릭터 외형 이탈 | panel-validator C1 REGEN → character_id 확인·식별 표식 강조 후 재렌더 |
| 서버 도달 불가/모델 API 비정상 | 사전 점검(`/api/image/models` 200) 실패 → 사용자에게 서버/SSH 상태 확인 요청, 렌더 보류 |
| 패널 50개 미만 | episode-outliner/panel-director에게 비트 추가 분할 요청 |
| 반전 불명확(QA REDO) | 시나리오팀(twist-master/script-editor) 또는 letterer로 피드백 후 재작업 |
| 데이터 충돌 | 출처 병기, 삭제 금지 |
| 무한 재작업 | 패널당 재생성 최대 3회, 단계별 재작업 루프 최대 2회. 초과 시 현 상태로 진행하고 한계를 보고 |

## 테스트 시나리오

### 정상 흐름
1. 사용자: "트렌드 반영해서 웹툰 1화 만들어줘."
2. Phase 1: brief 기록, `_workspace/` 생성.
3. Phase 2: 리서치팀 5명 → trend-brief.md.
4. Phase 3: 시나리오팀 9명 → script_final.md (반전 1개+, 50+ 패널 분량).
5. Phase 4: 비주얼팀 9명 → 레퍼런스 시트 선행 + character_id 등록 → 50+ panel PNG(텍스트 없는 아트, 서버 큐 배치 렌더, character_id IP-Adapter) → panel-validator 6축 검증-재생성 루프로 전 패널 통과 → validation.md.
6. Phase 5: 조립검수팀 4명 → 한글 말풍선 CSS 오버레이를 얹은 index.html + qa PASS → RELEASE/ep01/.
7. 결과: `RELEASE/ep01/index.html` 세로 스크롤 웹툰(한글 말풍선 오버레이) + 다음 화 시드.

### 에러 흐름 (배경 급변 + 구도 붕괴 재생성)
1. Phase 4 렌더 후 panel_023의 배경이 같은 씬(도로)인데 실내로 나오고, panel_031이 strength 과다로 정면 상반신 초상화로 붕괴.
2. panel-validator가 C2(023)·C4(031) REGEN 판정 → validation.md에 사유·수정 지시 기록.
3. prompt-smith가 023에 장소 토큰(LOC_*) 강화, 031에 ip_adapter_strength를 0.4~0.5로 낮추고 shot(wide) 재명시·시드 변경 → 담당 panel-artist가 그 2장만 재렌더.
4. panel-validator 재검증: 023 ACCEPT, 031도 구도 복원 ACCEPT. (한글 대사는 조립 오버레이가 보장하므로 텍스트 정확성은 이 단계에서 다루지 않는다.)
5. 전 패널 통과 후 조립 진행 — letterer 스키마로 한글 말풍선 오버레이를 얹고 qa_report·RELEASE 노트에 플래그 패널이 있으면 한계 명시.

## 후속 작업 가이드

- "다음 화" → Phase 0 case 2(새 회차). 세계관/스타일/연속성 재사용, 03_episode 이후만 신규.
- "반전 더 강하게" → 시나리오팀 부분 재실행(twist-master, script-editor) → 영향 하위 단계 재실행.
- "패널 N번 다시" → 비주얼팀 부분 재실행(prompt-smith 보강 + 해당 panel-artist 재렌더 + panel-validator 재검증) → 재조립.
- 같은 유형 피드백 2회+ 반복 시 해당 스킬/에이전트 정의 개선을 제안(하네스 진화). 변경은 CLAUDE.md 변경 이력에 기록.
