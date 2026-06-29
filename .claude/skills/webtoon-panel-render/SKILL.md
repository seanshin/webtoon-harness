---
name: webtoon-panel-render
description: "웹툰 패널 이미지를 로컬 GPU 서버(WeRU.B 이미지 API)로 배치 렌더링하는 스킬. 패널 렌더 전 캐릭터 레퍼런스를 먼저 렌더해 character_id(IP-Adapter)로 등록하고, 패널 프롬프트 목록(ep{NN}_prompts.md)에 일관성 토큰·character_id·씬 장소 토큰을 주입해 배치 생성한다. 한글 말풍선은 이미지에 굽지 않고 말풍선 자리만 비워둔 채 그리며(한글은 조립 단계 HTML 오버레이가 얹음), panel-validator의 생성-검증 루프로 기준 만족까지 재렌더한다. 0바이트·손상·md5 중복 PNG를 재시도한다. '패널 렌더링', '웹툰 이미지 생성', '레퍼런스 시트', '패널 이미지 배치 생성', '50장 그리기', '패널 그려', 그리고 후속 작업 '패널 다시 그려/재렌더/수정/일부만 다시'에도 반드시 이 스킬을 사용. 단일 단발 이미지 생성은 WeRU.B API를 직접 호출하는 편이 빠르다."
---

# Webtoon Panel Render — 레퍼런스(character_id) → 아트 렌더 → 검증 루프

웹툰 한 회차의 50+ 패널을 **로컬 GPU 서버(WeRU.B 이미지 API)**로 배치 렌더링하는 스킬. prompt-smith가 만든 패널 프롬프트 목록을 입력으로, 일관성을 지키며 PNG를 양산하고 검증한다. 렌더는 `scripts/weru_imagegen.py`(SSH 경유 API 호출 CLI)로 수행한다.

> **백엔드 = 사용자 로컬 서버.** 외부 codex/OpenAI를 쓰지 않는다. `seanshin/WeRUBLLMManager`(WeRU.B AI Server Admin, RTX 5080)의 이미지 API를 SSH 무암호 키로 호출한다. 모델/일관성/배치 능력이 codex보다 우수하다.

핵심 4원칙:
1. **레퍼런스 먼저(일관성 SSOT).** 패널을 그리기 전에 캐릭터 레퍼런스를 렌더하고 **`character/create`로 등록해 `character_id`를 확정**한다. 이후 모든 패널은 그 `character_id`(IP-Adapter)로 같은 인물을 유지한다. 텍스트 토큰만으로는 매번 다른 얼굴이 나온다.
2. **아트만 그린다 — 텍스트는 굽지 않는다.** 로컬 모델은 이미지 안 한글(CJK)을 못 그린다. 그래서 말풍선·대사·효과음을 **이미지에 굽지 않고**, 말풍선이 들어갈 **여백만 비워둔 채** 작화만 렌더한다. 한글 대사는 **조립 단계에서 HTML/CSS 오버레이**가 얹는다(letterer 명세 → episode-compositor). negative 프롬프트에 `text, speech bubble, caption, watermark`를 넣어 이미지 내 글자를 억제한다.
3. **배경 씬 단위 고정.** 씬별 장소 토큰(LOC_*)을 같은 scene_id의 모든 패널에 주입해 배경 급변(도로→실내 등)을 막는다.
4. **검증-재생성 루프.** panel-validator가 패널을 6축으로 검사하고 미달분을 기준 만족까지 되돌려 재렌더한다.

## 사전 점검 (회차당 1회)

로컬 서버 도달성을 확인한다(렌더 도중 멈추지 않도록 시작 전에).

```bash
ssh -p 32200 weruby@121.161.70.94 "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8585/api/image/models"
# 200 이면 정상. 아니면 사용자에게 서버/SSH 상태 확인을 요청한다.
```

접속 정보는 `scripts/weru_imagegen.py` 상단(환경변수 `WERU_SSH/WERU_PORT/WERU_API`로 덮어쓰기 가능). 기본 `weruby@121.161.70.94:32200` → `http://127.0.0.1:8585`.

## 모델·일관성 규약 (PoC 검증값)

- **작화 기본**: `model=dreamshaper`, `style=illustration` — 한국 웹툰 만화체. (대안: `animagine`/`anime` = 일본 애니풍.)
- **캐릭터 일관성 = `character_id`(IP-Adapter) + 샷별 강도**:
  | 샷 종류 | ip_adapter_mode | ip_adapter_strength |
  |--------|-----------------|---------------------|
  | 와이드·풀바디·액션 | `full` | **0.4** |
  | 감정 클로즈업 | `face` | **0.5** |
  - **strength ≥ 0.6 금지** — 구도·표정이 정면 상반신으로 붕괴한다(PoC에서 0.7이 모든 패널을 비슷한 초상화로 만들었다). 0.4~0.5가 "같은 인물, 다른 샷"을 만든다.
  - `character_id`는 **SDXL 계열만 지원**(dreamshaper/animagine/sdxl/juggernaut/realvis). flux는 IP-Adapter 미지원 → 빠른 프로토타입에만.
- **텍스트 금지**: negative에 `text, speech bubble, caption, signature, watermark`. (서버가 "AI 생성" 워터마크를 자동 삽입하니 그 외 글자만 막으면 된다.)
- **시드**: `seed`로 재현 가능. 재렌더 시 시드를 바꿔 변주한다.

## 0단계 — 캐릭터 레퍼런스 렌더 + character_id 등록 (ref-sheet-artist)

패널보다 먼저, 주요 캐릭터의 **대표 레퍼런스(정면 상반신, 깨끗한 외형)**를 렌더하고 등록한다. 이것이 모든 패널 일관성과 검증의 닻이다.

- 입력: `_workspace/04_visual/character-sheets.md`(불변 토큰), `style-bible.md`(작화 스타일).
- 캐릭터마다:
  1. 대표 레퍼런스 1장을 렌더 — 글로벌 작화 토큰 + 캐릭터 불변 토큰 + "front view, upper body, neutral expression, clean lineart, plain background, character reference". 식별 표식(점/흉터/팔찌 등)을 또렷이, 좌/우 위치 고정. **텍스트 없이**(`text, watermark` negative).
  2. 그 PNG를 `weru_imagegen.py register`로 등록해 `character_id`를 받는다.
  ```bash
  python3 .claude/skills/webtoon-panel-render/scripts/weru_imagegen.py \
    register --image _workspace/04_visual/refs/{IDTAG}_ref.png --name {idtag} --tags webtoon,{role}
  # → {"character_id":"...", ...}
  ```
- 저장: `_workspace/04_visual/refs/`(회차 폴더가 아니라 **시리즈 자산**, 다음 회차 재사용). `refs/INDEX.md`에 캐릭터별 **`character_id`** + 레퍼런스 경로 + 핵심 외형 한 줄 + 확정 여부를 기록.
- 등록 후 동일 `character_id`로 표정/포즈 2~3장을 시험 렌더해 일관성을 육안 확인. 흔들리면 레퍼런스를 다시 골라 재등록.
- 확정 시 `INDEX.md`(특히 `character_id`)를 prompt-smith·panel-validator에 인계.
- **후속 회차**: refs/INDEX.md의 `character_id`가 이미 있으면 재등록하지 않고 재사용(시리즈 일관성). 신규 캐릭터만 추가 등록.

## 입력 — 패널 프롬프트 목록

`_workspace/04_visual/ep{NN}_prompts.md`를 Read한다. 각 패널은 다음 형식이다:

```
### panel_001
- scene_group: A
- scene_id: S2 / location: LOC_CLASSROOM
- shot: wide            # wide|full|action → full/0.4 ; close|emotion → face/0.5
- character_ids: [jiho]
- prompt: "<글로벌 스타일 + 장소 토큰 + 구도/감정/상태색 — 영어, 텍스트/말풍선 없음, 말풍선 자리 비움>"
- negative: "text, speech bubble, caption, watermark, ..."
- output: panel_001.png
```

prompt-smith가 이 목록과 함께 **잡 JSON**(`ep{NN}_jobs.json`)을 만든다 — 각 패널을 `weru_imagegen.py gen`이 먹는 형식으로:

```json
[
  {"output":"panel_001.png","prompt":"...","model":"dreamshaper","style":"illustration",
   "negative_prompt":"text, speech bubble, caption, watermark, ...",
   "character_id":"<jiho-uuid>","ip_adapter_mode":"full","ip_adapter_strength":0.4,
   "width":832,"height":1216,"seed":1001}
]
```

## 일관성 점검 (렌더 전 필수)

각 잡이 다음을 포함하는지 확인한다. 누락·모호하면 prompt-smith에 보강 요청:
1. **작화 스타일** — `model`/`style` + style-bible 키워드가 프롬프트에 반영됐는가.
2. **등장 캐릭터의 `character_id`** — refs/INDEX.md의 확정 UUID. (다중 캐릭터 패널은 주연 1명을 character_id로, 나머지는 외형 토큰으로.)
3. **샷별 IP-Adapter** — `shot`에 맞는 mode/strength(위 표). strength ≥ 0.6 금지.
4. **씬 장소 토큰(LOC_*)** — 같은 scene_id의 모든 패널에 동일 배경 토큰.
5. **텍스트 억제 + 말풍선 여백** — negative에 `text, speech bubble`, 프롬프트에 "empty space for speech bubble"(letterer가 지정한 위치 쪽).

character_id·장소 토큰 없는 패널은 렌더하지 않는다 — 다시 그리는 비용이 더 크다.

## 핵심 — 배치 렌더링

서버는 **큐 기반**(최대 1만 건, VRAM 경합 없이 순차 처리)이라 codex 같은 동시 세션 한도를 걱정할 필요가 없다. **한 회차 전체(또는 scene 그룹)를 한 번에 큐에 넣는다.**

```bash
python3 .claude/skills/webtoon-panel-render/scripts/weru_imagegen.py \
  gen --jobs _workspace/04_visual/ep{NN}_jobs.json \
      --out-dir _workspace/05_panels/ep{NN}
```

- 헬퍼가 모든 잡을 큐에 등록 → 완료를 백오프 폴링(서버 레이트리밋 429 자동 대기) → 각 PNG를 `output` 파일명으로 다운로드한다.
- 출력 한 줄씩 `<output>\t<status>\t<server_filename>`. 실패 잡이 있으면 stderr에 목록 + exit 2.
- **부분 렌더**: 재렌더할 패널만 담은 잡 JSON을 따로 만들어 같은 명령으로 돌린다(전체 재실행 금지).

### 분량·소요 시간 기대치

| 패널 수 | 예상 렌더 시간(서버 순차) |
|--------|--------------------------|
| 50장 | dreamshaper ~6s/장 ≈ 5~6분 (+ 다운로드) |
| 60장 | ≈ 7분 |

LCM 모드(`lcm_mode:true` 또는 `style:lcm-fast`)로 2~3배 가속 가능(품질 약간 절충). 사용자에게 렌더가 수 분 걸림을 미리 알린다.

## 렌더 후 무결성 검증 (필수)

```bash
ls -la _workspace/05_panels/ep{NN}/*.png
file _workspace/05_panels/ep{NN}/*.png                    # 모두 "PNG image data" 인지
find _workspace/05_panels/ep{NN} -name '*.png' -size 0    # 0바이트 목록 (비어야 정상)
md5 -r _workspace/05_panels/ep{NN}/panel_*.png | awk '{print $1}' | sort | uniq -d  # md5 중복 (비어야 정상)
```

처리:
- **0바이트/손상/다운로드 실패 PNG** → 그 패널만 다시 렌더(헬퍼 stderr의 실패 목록 사용).
- **md5 중복 PNG** → 중복 패널을 삭제하고 시드를 바꿔 단독 재렌더.
- **누락 패널 번호** → prompts 목록과 실제 PNG 목록 대조 후 빠진 번호만 렌더.
- 모든 패널이 존재·유효·고유하면 1차 무결성 통과 → 아래 검증-재생성 루프로.

## 검증-재생성 루프 (panel-validator) — 기준 만족까지 재렌더

무결성만으로는 부족하다. 디퓨전은 같은 프롬프트에도 엉뚱한 배경·다른 얼굴·잘못된 구도를 낸다. 렌더 직후 **패널 단위로** 6축을 검사하고 미달분을 되돌려 재렌더한다. 통과 패널만 조립으로 간다.

**6축 검사** (각 패널을 Read로 열어 육안 + 스크립트):
1. **C1 캐릭터 일관성** — refs의 `character_id` 기준 인물과 같은 사람인가(헤어/눈/체형/식별 표식·좌우). 의도된 변형은 예외.
2. **C2 배경/장소 연속성** — 배경이 그 패널의 scene_id/location(LOC_*)과 일치하는가. 같은 씬인데 장소 급변하면 REGEN.
3. **C3 말풍선 여백 — 텍스트 없음 확인** — 패널에 **굽힌 글자/말풍선이 없어야** 한다(있으면 REGEN: negative 강화·재렌더). 그리고 letterer가 지정한 위치에 **말풍선 오버레이가 들어갈 여백/저복잡도 공간**이 확보됐는가(캐릭터 얼굴·핵심 작화를 가리지 않도록). 한글 정확성 자체는 조립 단계 오버레이에서 보장되므로 여기서는 **"이미지에 글자 없음 + 오버레이 공간 확보"** 만 본다.
4. **C4 프롬프트 충실도** — 샷 사이즈/앵글/구도/감정/상태색이 의도대로인가. (구도 붕괴 = strength 과다 신호 → 0.4~0.5로 낮춰 재렌더.)
5. **C5 장면 흐름** — 앞뒤 패널과 이어 보아 인물·시선·동선이 자연스러운가.
6. **C6 기술 무결성** — 0바이트/손상/md5 중복 아님, 경로·번호 정확.

**루프**: 패널마다 ACCEPT / REGEN(사유+수정 지시). REGEN → prompt-smith가 그 패널 잡만 보강(배경 급변→장소 토큰 강화, 구도 붕괴→strength↓·샷 재명시, 외형 이탈→character_id 확인·식별 표식 강조, 텍스트 새어나옴→negative 강화) → 그 패널만 시드 변경 재렌더 → 재검사. **패널당 최대 3회.** 3회 후에도 미달이면 가장 나은 버전을 **ACCEPT-FLAG**(통과+한계 명시)로 마감하고 `ep{NN}_validation.md`에 기록.

출력: `_workspace/04_visual/ep{NN}_validation.md`(패널별 판정·6축 결과·재생성 횟수·플래그·각 패널의 말풍선 오버레이 가용 공간 메모 → letterer/compositor에 인계).

## 일부만 다시 그리기 (후속 작업)

quality-reviewer가 FIX/REDO로 지정한 패널만 재렌더한다. 전체를 다시 그리지 않는다.
1. qa_report.md에서 REDO 패널 번호와 수정 지시를 읽는다.
2. 해당 패널 잡에 수정 지시 반영(prompt-smith와 조율) + 시드 변경.
3. 그 패널들만 담은 잡 JSON으로 `weru_imagegen.py gen` 재실행 → 재검증.
4. 같은 패널을 2회 재렌더 후에도 실패하면 경고와 함께 통과시키고 보고서에 명시.

## 안티패턴

- **이미지에 한글/말풍선 굽기** — 로컬 모델은 한글을 못 그린다. negative로 텍스트를 억제하고 말풍선은 오버레이로. `no text`를 빼면 깨진 가짜 글자가 새어 나온다.
- **strength ≥ 0.6 사용** — 모든 패널이 비슷한 정면 상반신으로 붕괴(PoC 검증). 와이드 0.4 / 클로즈업 face 0.5 고정.
- **flux로 캐릭터 일관성 시도** — flux는 IP-Adapter 미지원. 일관성 필요 패널은 SDXL(dreamshaper 등).
- **레퍼런스/character_id 없이 렌더** — 외형이 흔들려 재작업 비용 폭증. character_id 확정 전, 장소 토큰 주입 전에 패널을 렌더하지 않는다.
- **동일 출력 파일명 중복** — 잡의 `output`이 겹치면 덮어쓴다. 전부 달라야 함.
- **md5 중복 미검사** — 드물게 한 패널이 다른 패널 이미지를 받는 사고를 놓친다. 크기/헤더만 보지 말 것.
- **검증 없이 조립 직행** — panel-validator 6축 통과 전 패널은 조립에 넘기지 않는다.
- **말풍선 오버레이 공간 무시** — 인물 얼굴 위에 글자가 얹히면 가독·작화가 무너진다. 렌더 시 letterer 지정 위치에 여백을 확보한다.

## 출력

- `_workspace/05_panels/ep{NN}/panel_001.png` … `panel_0NN.png` (50+장, **텍스트 없는 아트**)
- 렌더 요약(생성/재시도/실패 패널 수)을 episode-compositor와 리더에게 보고.
- 한글 말풍선은 episode-compositor가 letterer 명세로 오버레이한다(이 스킬은 아트만 책임).
