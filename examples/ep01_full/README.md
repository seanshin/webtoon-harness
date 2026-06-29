# 예제 — 심야 편의점 1화 (풀버전 70컷)

이 하네스로 실제 제작·검증한 **70컷 풀 에피소드**의 생성기와 뷰어 빌더입니다.
비트시트(스토리 데이터) → `jobs.json` + `lettering.json` 자동 생성 → 로컬 GPU 렌더 →
세로 스크롤 자가완결 HTML 조립까지의 워크플로우를 재현 가능한 형태로 보존합니다.

> 산출물(렌더된 PNG, 거대한 base64 `index.html`)은 `_workspace/`(gitignore)에 생성되므로
> 저장소에는 **스크립트만** 추적합니다.

## 파일

| 파일 | 역할 |
|------|------|
| `gen_ep01full.py` | 비트시트(`BEATS`) → `ep01full_jobs.json` + `ep01full_lettering.json` 생성기. 샷→IP-Adapter 강도 자동 매핑, animagine 강화 negative 주입, 긍정 프롬프트 "speech bubble" 금지 규약을 강제한다. 새 회차는 `BEATS`만 갈아끼우면 된다. |
| `build_viewer.py` | 텍스트 없는 패널 PNG + `lettering.json` → CSS 말풍선 오버레이를 얹은 세로 스크롤 `index.html`. 패널을 base64로 임베드해 자가완결. CLI 인자로 어떤 회차에도 재사용. |

## 실행

```bash
# 1) 비트시트 → jobs + lettering 생성
python3 gen_ep01full.py
#   → _workspace/04_visual/ep01full_jobs.json, ep01full_lettering.json

# 2) 로컬 GPU 렌더 (WeRU.B). 등장인물은 먼저 character/create로 등록해 둔다.
python3 ../../.claude/skills/webtoon-panel-render/scripts/weru_imagegen.py \
    gen --jobs _workspace/04_visual/ep01full_jobs.json \
        --out-dir _workspace/05_panels/ep01_full

# 3) 세로 스크롤 뷰어 조립
python3 build_viewer.py \
    --panels-dir ../../_workspace/05_panels/ep01_full \
    --lettering  ../../_workspace/04_visual/ep01full_lettering.json \
    --out index_full.html --title "심야 편의점 — 1화" --count 70
```

## lettering.json 포맷

```json
{
  "panel_001.png": [
    ["narration", "", "비 오는 날 새벽 3시. 손님은 늘 그 시간에 온다.", "7%", "10%", "none", "80%"]
  ],
  "panel_012.png": [
    ["speech", "지호", "어서오세요.", "6%", "42%", "bottom-right", "52%"]
  ]
}
```

엔트리 순서 = `[type, speaker, text, top, left, tail, max_width]`.
`type` = `speech | thought | shout | narration | sfx`,
`tail` = `bottom-left | bottom-right | none`, 위치/폭은 CSS 퍼센트 문자열.

## 검증된 운영값

샷별 IP-Adapter 강도, 만화 모델 강화 negative, 소품 인서트 교정 등은
저장소 루트 [`README.md`](../../README.md)의 **"검증된 렌더 운영값"** 섹션을 참조.
