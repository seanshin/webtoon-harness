# Changelog

본 프로젝트의 주요 변경 이력. [Semantic Versioning](https://semver.org/lang/ko/)을 따른다.

## [v1.1.0] — 2026-06-29

### Added — Claude 없이 도는 독립 CLI
- `examples/standalone_cli/werubtoon.py` — WeRU.B 서버의 **로컬 LLM(qwen2.5:14b)을 두뇌**로 써서
  로그라인 한 줄 → 비트 작성 → 패널 렌더 → 세로 스크롤 뷰어까지 **Claude 미사용** 완전 자율 생성.
  - `ssh_post`: `/api/generate` NDJSON 스트림 누적
  - `synth`: 검증된 운영값(샷별 IP-Adapter, 강화 negative, 인서트 객체강제 프리셋,
    bubble-space→CSS 좌표)을 코드로 박제
  - `weru_imagegen.py` + `build_viewer.py`를 서브프로세스로 오케스트레이션
- `examples/standalone_cli/README.md` — CLI 사용법·파이프라인·두뇌 교체 메모.

### Changed — LLM 두뇌 견고화 (배치 누적)
- `llm_beats`를 단일 호출 → **배치 누적**으로 교체. qwen이 단일 호출에서 목표 컷 수를 줄이고
  (예: 50→18) 대사를 통째로 누락하던 문제를 해결.
  - ~8컷씩 이어 생성하며 목표 컷 수 강제(연속성 컨텍스트 전달)
  - 비인서트 컷 대사 필수화 + 누락 시 내레이션 폴백
  - 배치 파싱 실패 재요청 + stale 가드로 무한루프 방지

### Validated
- **'심야 편의점' 50컷 풀 에피소드** E2E 생성: 비트 50/50(대사 포함), 패널 50/50
  (일시 실패 10컷 재렌더 후 누락 0), 지호·유나 IP-Adapter 일관성 유지.

## [v1.0.0] — 2026-06-29

### Added
- 검증된 렌더 운영값 섹션(70컷 풀 에피소드 실측) — 샷별 IP-Adapter, animagine 강화 negative,
  품질 프로파일, 소품 인서트 객체강제 프리셋.
- `examples/ep01_full/` — 70컷 풀 에피소드 비트시트 생성기 + 뷰어 빌더.
- Webtoon Studio 기획: WeRUB(blog, Next.js) 소설 기능 형제 탭으로 통합하는
  6단계 UX 설계(`docs/webtoon-studio-ux.md`) + 통합 스펙(`docs/webtoon-werub-integration.md`).
