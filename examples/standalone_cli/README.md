# 🤖 werubtoon — Claude 없이 도는 독립 웹툰 CLI

> **"클로드를 빼고는 진행이 안되지 않나?"** 에 대한 답.
> 하네스(`.claude/agents`·`skills`)는 Claude가 두뇌였지만, 이 CLI는 그 두뇌를
> **WeRU.B 서버의 로컬 LLM**(`qwen2.5:14b` 등)으로 대체한 완전 자율 파이프라인이다.
> 로그라인 한 줄만 주면 비트 작성 → 패널 렌더 → 세로 스크롤 뷰어까지 사람·Claude 개입 0.

## 파이프라인

```
로그라인 ──[WeRU.B /api/generate]──▶ 비트 JSON ──synth──▶ jobs/lettering
        ──[weru_imagegen.py]──▶ 패널 PNG ──[build_viewer.py]──▶ index.html
```

WeRU.B **서버 하나**가 두뇌(LLM)와 손(이미지 렌더)을 모두 자급한다.

## 사용

```bash
python3 werubtoon.py \
  --logline "편의점 알바생이 단골이 유령임을 깨닫는다" \
  --cuts 6 --title "심야 편의점" --out ./out_ep
```

| 플래그 | 설명 |
|---|---|
| `--logline` | 한 줄 로그라인(필수) |
| `--cuts` | 컷 수(기본 6) |
| `--title` | 뷰어 제목 |
| `--out` | 작업 디렉토리(필수) |
| `--cast` | 추가 캐스트 `"name=charid,name2=charid2"` |
| `--skip-render` | 비트/잡만 생성(렌더 생략) |

환경변수: `WERU_SSH` / `WERU_PORT` / `WERU_API` / `WERU_LLM`
(`weru_imagegen.py`와 동일 기본값: `weruby@121.161.70.94`, `32200`, `http://127.0.0.1:8585`, `qwen2.5:14b`)

## 검증된 운영값을 그대로 코드화

`synth()`가 README "검증된 렌더 운영값"을 자동 적용한다:

- **샷별 IP-Adapter** — `wide/full→{full,0.4}`, `close/emotion→{face,0.5}`, **≥0.6 금지**(인물 붕괴).
- **강화 negative** — animagine 가짜 말풍선/gibberish 제거 토큰.
- **인서트(소품) 컷** — 객체강제 프리셋(`people/person/shelves` negative).
- **bubble-space** — 비트의 `bspace`(top/bottom/tl/tr/bl/center) → CSS 말풍선 좌표.

## 두뇌 교체 메모

- `/api/generate`는 **NDJSON 스트림** — `ssh_post()`가 `response` 필드를 이어붙인다.
- LLM JSON이 깨질 때를 대비해 `repair_json_array()`(배열 추출·trailing comma 복구) + 재요청 루프.
- 미등록 캐릭터 이름은 IP 없이 렌더(드리프트 방지보다 무드 우선).

## 관계

- 두뇌·각색 서버 능력: 메모리 `weru-server-capabilities`, `webtoon-local-imagegen`.
- 웹 GUI 버전(WeRUB blog 통합): `docs/webtoon-werub-integration.md`.
- 이 CLI는 그 통합의 **참조 구현/스모크 테스트**이기도 하다.
