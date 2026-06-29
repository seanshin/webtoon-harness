# 🎬 Webtoon Harness — 웹툰 자동 제작 하네스

> 트렌드 조사부터 세로 스크롤 뷰어 완성까지, 웹툰 한 회차를 **AI 에이전트 팀**이 단계별로 만들어내는 Claude Code 하네스.

**27개 전문 에이전트**와 **6개 스킬**로 구성되며, 인기 웹툰 트렌드 조사 → 대사 위주·고긴장·매 회차 반전 시나리오 작성 → 캐릭터 레퍼런스 시트 선행 렌더 → 회차당 50+ 패널을 **로컬 GPU 서버(WeRU.B 이미지 API)**로 배치 렌더(말풍선 자리는 비워 둠) → 생성-검증 루프로 재생성 → 한글 대사를 **HTML 오버레이**로 얹어 세로 스크롤 뷰어 조립까지 전 과정을 자동화합니다.

![Webtoon Harness 개요](docs/images/01_overview.png)

---

## ✨ 특징

- **27 에이전트 / 4 단계 팀**: 리서치 → 시나리오 → 비주얼 → 조립검수. 각 Phase마다 팀을 재구성하며 운영합니다.
- **레퍼런스 시트 선행 렌더**: 캐릭터 다각도·표정 레퍼런스를 먼저 렌더해 회차 간 외형 일관성의 단일 진실원천(SSOT)을 확보합니다.
- **한글 말풍선 HTML 오버레이**: 로컬 모델은 한글(CJK)을 못 그리므로 작화만 렌더하고 말풍선 자리를 비운 뒤, 한글 대사를 조립 단계 HTML/CSS 오버레이로 정확히 얹습니다.
- **배치 렌더 + 생성-검증 루프**: 로컬 이미지 서버 큐에 한 회차 전체를 한 번에 넣어 순차 렌더하고, `panel-validator`가 6축 검증 후 기준 미달 패널만 재생성합니다.
- **연속성 관리**: 회차를 넘어 캐릭터 외형·설정·떡밥(복선)을 누적 추적합니다.

---

## 📁 구조

```
.claude/
├── agents/                      # 27개 전문 에이전트 정의
│   ├── trend-scout.md           # 리서치팀
│   ├── concept-architect.md     # 시나리오팀
│   ├── art-director.md          # 비주얼팀
│   ├── panel-validator.md       # 생성-검증 게이트키퍼
│   ├── episode-compositor.md    # 조립검수팀
│   └── ... (총 27개)
└── skills/                      # 6개 방법론 스킬
    ├── webtoon-orchestrator/    # ⭐ 메인 오케스트레이터 (진입점)
    ├── webtoon-trend-research/  # 트렌드 리서치 방법론
    ├── webtoon-scenario/        # 시나리오·대본 집필
    ├── webtoon-panel-breakdown/ # 패널 분해·스타일/일관성 토큰
    ├── webtoon-panel-render/    # 로컬 GPU 서버(WeRU.B) 배치 렌더
    └── webtoon-assembly/        # 세로 스크롤 조립·검수·패키징
```

---

## 👥 에이전트 팀 (27명, 4팀)

| 팀 | 팀원 | 역할 |
|----|------|------|
| **리서치팀** | trend-scout, platform-ranker, audience-analyst, hook-analyst, trend-synthesizer | 장르 동향·플랫폼 랭킹·독자 반응·후킹/반전 역설계 → 기획 브리프 종합 |
| **시나리오팀** | concept-architect, worldbuilder, character-designer, series-plotter, twist-master, tension-engineer, episode-outliner, dialogue-writer, script-editor | 하이콘셉트·세계관·캐릭터·시리즈 아크·매 회차 반전·긴장 곡선·비트시트·대사 대본·교정 |
| **비주얼팀** | art-director, ref-sheet-artist, panel-director, letterer, prompt-smith, panel-artist-a/b/c, panel-validator | 스타일 바이블·레퍼런스 시트·샷리스트·레터링·프롬프트 합성·패널 렌더·6축 검증 루프 |
| **조립검수팀** | episode-compositor, quality-reviewer, continuity-manager, showrunner | 세로 스크롤 뷰어 조립·QA 검수·연속성 관리·사인오프 패키징 |

### 🔍 리서치팀 — 4명 조사 → 1명 종합

4명의 조사자(트렌드·플랫폼 랭킹·독자 반응·후킹/반전)가 병렬로 조사하고, synthesizer가 하나의 기획 브리프로 종합합니다.

![리서치팀](docs/images/02_research.png)

### ✍️ 시나리오팀 — 컨셉에서 최종 대본까지

하이콘셉트에서 출발해 세계관·캐릭터·시리즈 아크를 거쳐 반전 계획과 긴장 곡선을 병렬 설계하고, 비트시트→대본→최종본으로 수렴합니다. **매 회차 반전**과 **50+ 패널 분량**을 보장합니다.

![시나리오팀](docs/images/03_scenario.png)

### 🎨 비주얼팀 — 레퍼런스 선행 + 생성-검증 루프

아트 디렉터의 스타일 바이블 → 캐릭터 레퍼런스 시트 선행 렌더(character_id 등록) → 샷리스트·레터링 → 프롬프트 합성 → 3명의 아티스트가 로컬 GPU 서버(WeRU.B 이미지 API)로 패널을 배치 렌더 → panel-validator가 6축 검증·재생성 루프를 돌립니다. 말풍선은 이미지에 굽지 않고 자리만 비워두며, 한글 대사는 조립 단계 HTML 오버레이로 얹습니다.

![비주얼팀](docs/images/04_visual.png)

### 🧩 조립검수팀 — 조립에서 릴리스까지

텍스트 없는 패널을 세로 스크롤 뷰어로 조립하며 한글 말풍선을 HTML 오버레이로 얹고, QA 검수·연속성 관리를 거쳐 showrunner가 최종 사인오프 후 RELEASE로 패키징합니다.

![조립검수팀](docs/images/05_assembly.png)

---

## 🔄 워크플로우

```
trend-brief.md
   └→ concept → world → characters → series-arc → {twist-plan, tension-curve}
                                                      └→ beatsheet → script → script_final
script_final + characters
   └→ style-bible(+장소토큰, 말풍선 오버레이 규약) / character-sheets
        └→ refs/*.png + character_id (레퍼런스 시트, 패널 전 선행)
        └→ shotlist(scene_id/location/shot) + lettering(HTML 오버레이 말풍선 명세)
              └→ prompts + jobs.json(스타일+장소+character_id+말풍선 여백)
                    └→ panel_*.png ⇄ panel-validator 6축 검증-재생성 루프
                          └→ validation.md (전 패널 통과)
panel_*.png(텍스트 없음) → index.html(한글 말풍선 오버레이) → qa_report → RELEASE/ep{NN}/
```

**6단계 실행:** Phase 0(컨텍스트 확인) → 1(준비) → 2(리서치) → 3(시나리오) → 4(비주얼) → 5(조립·검수) → 6(마무리).

---

## 🚀 사용 방법

이 저장소는 [Claude Code](https://claude.ai/code) 하네스입니다. `.claude/` 디렉토리를 작업 프로젝트 루트에 두고 Claude Code를 실행하세요.

```bash
# 1) 하네스를 프로젝트에 배치
git clone https://github.com/revfactory/webtoon-harness.git
cp -r webtoon-harness/.claude /path/to/your-project/

# 2) 해당 프로젝트에서 Claude Code 실행 후
```

그다음 Claude Code 세션에서 자연어로 요청합니다:

- `"트렌드 반영해서 웹툰 1화 만들어줘"` — 전체 파이프라인 실행
- `"다음 화 만들어"` — 세계관/스타일/연속성 재사용, 새 회차 생성
- `"이 회차 반전 더 강하게"` — 시나리오팀 부분 재실행
- `"패널 23번 다시 그려"` — 해당 패널만 재렌더 + 재검증

`webtoon-orchestrator` 스킬이 자동으로 트리거되어 단계별 에이전트 팀을 조율합니다.

### 요구 사항

- **Claude Code** (에이전트·스킬 실행 환경)
- **로컬 이미지 생성 서버** (WeRU.B 이미지 API, SSH 접근) — 패널 이미지 배치 렌더. `.claude/skills/webtoon-panel-render/scripts/weru_imagegen.py`가 SSH 무암호 키로 호출합니다.
  - 서버 도달성은 `ssh ... "curl -s .../api/image/models"`로 사전 점검합니다(접속 정보·환경변수는 `weru_imagegen.py` 상단 참조).

> 💡 이 저장소의 인포그래픽들은 16:9 비율 이미지 생성으로 제작했습니다.

---

## 🎯 설계 원칙

- **대사 위주·고긴장·매 회차 반전**: 내레이션을 최소화하고 캐릭터 대사·행동으로 긴장과 정보, 반전을 전달합니다.
- **회차당 50+ 패널**: 세로 스크롤 리듬에 맞춰 비트를 충분히 쪼갭니다.
- **일관성 우선**: 레퍼런스 시트 → 일관성 토큰 → 장소 토큰을 모든 프롬프트에 주입하고, md5 중복·배경 급변·한글 깨짐을 검증 루프로 잡습니다.
- **감사 추적**: 모든 중간 산출물을 `_workspace/`에 보존합니다.

---

## 📝 라이선스

[MIT](LICENSE)
