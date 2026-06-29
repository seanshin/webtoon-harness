#!/usr/bin/env python3
"""werubtoon — Claude 없이 도는 독립 웹툰 생성 CLI.

WeRU.B 서버 하나만으로 두뇌(LLM)+이미지(렌더)를 자급한다:
  로그라인 → [LLM /api/generate] 비트 JSON → jobs/lettering 합성
           → [weru_imagegen.py] 패널 렌더 → [build_viewer.py] 세로 스크롤 뷰어

Claude Code 하네스(.claude/agents·skills)는 Claude가 두뇌였지만, 이 CLI는
그 두뇌를 로컬 LLM(qwen2.5 등)으로 대체한 자율 파이프라인이다.

사용:
  python3 werubtoon.py --logline "편의점 알바생이 단골이 유령임을 깨닫는다" \\
      --cuts 6 --title "심야 편의점" --out ./out_ep
환경: WERU_SSH / WERU_PORT / WERU_API (weru_imagegen.py와 동일 기본값)
"""
import argparse, json, os, re, subprocess, sys, textwrap

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_SCRIPTS = os.path.normpath(os.path.join(HERE, "../../.claude/skills/webtoon-panel-render/scripts"))
WERU_IMAGEGEN = os.path.join(SKILL_SCRIPTS, "weru_imagegen.py")
BUILD_VIEWER = os.path.normpath(os.path.join(HERE, "../ep01_full/build_viewer.py"))

SSH = os.environ.get("WERU_SSH", "weruby@121.161.70.94")
PORT = os.environ.get("WERU_PORT", "32200")
API = os.environ.get("WERU_API", "http://127.0.0.1:8585")
LLM_MODEL = os.environ.get("WERU_LLM", "qwen2.5:14b")

# 검증된 운영값 (README "검증된 렌더 운영값"과 동일) ──────────────
LOC = {
 "EXT":   "exterior storefront of a brightly lit Korean convenience store at night, neon sign, wet rainy street",
 "CVS":   "interior of a brightly lit Korean convenience store at night, shelves, counter, cold fluorescent lighting",
 "STREET":"empty wet city street at deep night, rain, neon reflections",
}
SHOT = {"wide":"wide establishing shot, ","full":"full body shot, ","close":"close-up shot, ",
        "emotion":"extreme emotional close-up of the face, ","insert":"extreme close-up still-life insert shot, single object fills the frame, "}
QUAL = ", masterpiece, best quality, highly detailed, sharp focus, intricate details, cinematic moody lighting"
NEG = ("text, speech bubble, caption, watermark, purple hair, silver highlights, oversaturated, lowres, blurry, "
       "jpeg artifacts, bad anatomy, deformed, extra fingers, speech bubble, speech balloon, manga panel, comic book, "
       "comic panel, dialogue text, japanese text, caption box, sound effect text, manga, manhwa text")
INSERT_NEG = NEG + ", people, person, product shelves, store aisle, neon signs"
BS = {"top":("7%","10%","none","80%"),"bottom":("82%","10%","none","80%"),
      "tl":("6%","6%","bottom-left","52%"),"tr":("6%","42%","bottom-right","52%"),
      "bl":("60%","6%","bottom-left","52%"),"center":("44%","15%","none","70%")}
# 기존 등록 캐릭터 재사용(없으면 --cast로 덮어쓰기). 미지의 이름은 IP 없이 렌더.
DEFAULT_CAST = {"jiho":"e95ac39e-6f02-412c-9a95-9a06489ae677",
                "yuna":"08f8bba9-23e0-4f1e-9c6d-dd29046f6b5a"}


def ssh_post(path, payload):
    """WeRU.B에 POST. /api/generate는 NDJSON 스트림이라 response 필드를 이어붙인다."""
    data = json.dumps(payload, ensure_ascii=False)
    cmd = ["ssh", "-p", PORT, "-o", "ServerAliveInterval=15", SSH,
           f"curl -s -X POST {API}{path} -H 'Content-Type: application/json' -d @-"]
    p = subprocess.run(cmd, input=data, capture_output=True, text=True, timeout=300)
    out = p.stdout
    # NDJSON 누적
    chunks = []
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line, strict=False)
        except Exception:
            continue
        if "response" in obj:
            chunks.append(obj["response"])
    if chunks:
        return "".join(chunks)
    return out  # 비스트리밍 응답


def repair_json_array(txt):
    """LLM이 뱉은 텍스트에서 JSON 배열을 추출·복구한다."""
    m = re.search(r"\[.*\]", txt, re.S)
    s = m.group(0) if m else txt
    for attempt in (s, s.replace('"]}', '"}]}'), re.sub(r",\s*([\]}])", r"\1", s)):
        try:
            return json.loads(attempt, strict=False)
        except Exception:
            continue
    return None


SYS_PROMPT = ("You are a Korean webtoon director. You output ONLY valid JSON — no prose, no markdown fences. "
              "Use only these character ids for 'char': \"jiho\", \"yuna\", or null. "
              "EVERY non-insert cut MUST have at least one dialogue entry with a non-empty Korean 'ko'.")
SCHEMA_DOC = textwrap.dedent("""\
    각 원소 스키마:
    {"shot":"wide|full|close|emotion|insert",
      "loc":"EXT|CVS|STREET",
      "char":"jiho|yuna|null",
      "scene_en":"english visual description, NO text/letters/speech-bubble words",
      "bspace":"top|bottom|tl|tr|bl|center",
      "dialogue":[{"type":"speech|thought|narration|sfx","speaker":"이름 또는 빈칸","ko":"한글 대사"}]}
    규칙: 인서트(소품)컷만 dialogue 비움(char=null). 그 외 모든 컷은 dialogue 최소 1줄(빈 ko 금지).
    분위기는 차갑고 긴장. 대사는 짧고 자연스러운 구어체.""")


def _ask_batch(logline, total, sofar, need, retries=2):
    """다음 need개 컷을 이어서 생성. sofar=지금까지의 (idx,shot,char,ko요약) 리스트."""
    ctx = "\n".join(f"  #{i}: [{s}] {k}" for i, s, k in sofar) or "  (아직 없음)"
    base = textwrap.dedent(f"""\
        로그라인: "{logline}"
        전체 {total}컷짜리 세로 스크롤 웹툰을 만드는 중이다. 지금까지 작성된 컷:
        {ctx}

        이어서 **정확히 {need}개**의 다음 컷을 JSON 배열로만 출력하라(앞 내용과 연결, 중복 금지).
        {SCHEMA_DOC}
        {'이번이 마지막 묶음이다 — 마지막 컷은 여운/클리프행어로.' if need + len(sofar) >= total else ''}
        JSON 배열만 출력.""")
    user = base
    for i in range(retries + 1):
        txt = ssh_post("/api/generate", {"model": LLM_MODEL, "system": SYS_PROMPT, "prompt": user})
        arr = repair_json_array(txt)
        if arr and isinstance(arr, list):
            ok = [b for b in arr if isinstance(b, dict) and b.get("shot")]
            if ok:
                return ok
        user = base + "\n\n(직전 출력이 유효한 JSON 배열이 아니었다. 반드시 유효한 JSON 배열만.)"
        print(f"  ⚠ 배치 파싱 실패 — 재요청 {i+1}/{retries}", file=sys.stderr)
    return []


def _has_dialogue(b):
    return any((d.get("ko") or "").strip() for d in (b.get("dialogue") or []))


def llm_beats(logline, cuts):
    """로컬 LLM 두뇌로 비트를 '배치 누적'해 목표 컷 수·대사를 강제한다.

    qwen은 단일 호출에서 긴 구조화 출력의 개수를 줄이고 필드를 빠뜨린다.
    그래서 ~8컷씩 이어 생성하고, 대사 없는 비인서트 컷은 보정한다.
    """
    BATCH = 8
    beats, stale = [], 0
    while len(beats) < cuts and stale < 3:
        need = min(BATCH, cuts - len(beats))
        sofar = [(i + 1, b.get("shot", "?"),
                  " / ".join((d.get("ko") or "") for d in (b.get("dialogue") or []))[:40])
                 for i, b in enumerate(beats)]
        got = _ask_batch(logline, cuts, sofar, need)
        if not got:
            stale += 1
            continue
        stale = 0
        beats.extend(got)
        print(f"      …누적 {len(beats)}/{cuts}컷", file=sys.stderr)
    if not beats:
        raise SystemExit("LLM이 유효한 비트 JSON을 생성하지 못했습니다.")
    beats = beats[:cuts]
    # 대사 누락 비인서트 컷 1회 보정(개별 컷 재요청은 비용↑ → 내레이션 1줄 폴백)
    miss = [b for b in beats if b.get("shot") != "insert" and not _has_dialogue(b)]
    if miss:
        print(f"  ⚠ 대사 누락 {len(miss)}컷 — 내레이션 폴백 삽입", file=sys.stderr)
        for b in miss:
            b.setdefault("dialogue", []).append({"type": "narration", "speaker": "", "ko": "…"})
    return beats


def ipfor(shot):
    if shot in ("full", "wide"): return ("full", 0.4)
    if shot in ("close", "emotion"): return ("face", 0.5)
    return (None, None)


def synth(beats, cast):
    jobs, lettering = [], {}
    for i, b in enumerate(beats, 1):
        pid = f"panel_{i:03d}"
        shot = b.get("shot", "full"); loc = b.get("loc", "CVS")
        char = b.get("char"); char = None if char in (None, "null", "") else char
        scene = (b.get("scene_en") or "").strip()
        prompt = f"anime illustration style, {SHOT.get(shot, '')}{scene}, {LOC.get(loc, LOC['CVS'])}{QUAL}"
        job = {"output": f"{pid}.png", "panel_id": pid, "shot": shot,
               "prompt": prompt, "model": "animagine", "style": "illustration",
               "negative_prompt": INSERT_NEG if shot == "insert" else NEG,
               "width": 896, "height": 1280, "seed": 3000 + i, "steps": 30, "cfg": 6.5}
        mode, strength = ipfor(shot)
        cid = cast.get(char) if char else None
        if cid and mode:
            job["character_ids"] = [char]; job["character_id"] = cid
            job["ip_adapter_mode"] = mode; job["ip_adapter_strength"] = strength
        jobs.append(job)
        top, left, tail, mw = BS.get(b.get("bspace", "top"), BS["top"])
        rows = []
        for d in b.get("dialogue", []):
            rows.append([d.get("type", "speech"), d.get("speaker", ""), d.get("ko", ""), top, left, tail, mw])
            top = f"{int(top.rstrip('%')) + 13}%"
        lettering[f"{pid}.png"] = rows
    return jobs, lettering


def run(cmd):
    print("  $", " ".join(cmd))
    subprocess.run(cmd, check=True)


def main():
    ap = argparse.ArgumentParser(description="Claude 없이 WeRU.B LLM으로 웹툰 한 편을 만든다")
    ap.add_argument("--logline", required=True)
    ap.add_argument("--cuts", type=int, default=6)
    ap.add_argument("--title", default="웹툰")
    ap.add_argument("--out", required=True, help="작업 디렉토리")
    ap.add_argument("--cast", default="", help='추가 캐스트 매핑 "name=charid,name2=charid2"')
    ap.add_argument("--skip-render", action="store_true", help="비트/잡만 생성(렌더 생략)")
    a = ap.parse_args()

    cast = dict(DEFAULT_CAST)
    for kv in filter(None, a.cast.split(",")):
        k, v = kv.split("="); cast[k.strip()] = v.strip()

    os.makedirs(a.out, exist_ok=True)
    panels_dir = os.path.join(a.out, "panels"); os.makedirs(panels_dir, exist_ok=True)
    jobs_path = os.path.join(a.out, "jobs.json")
    letter_path = os.path.join(a.out, "lettering.json")
    viewer_path = os.path.join(a.out, "index.html")

    print(f"[1/4] 🧠 로컬 LLM({LLM_MODEL})로 {a.cuts}컷 비트 생성…")
    beats = llm_beats(a.logline, a.cuts)
    print(f"      비트 {len(beats)}컷 생성됨")
    for i, b in enumerate(beats, 1):
        kos = " / ".join(d.get("ko", "") for d in b.get("dialogue", []))
        print(f"      #{i} [{b.get('shot')}/{b.get('loc')}/{b.get('char')}] {kos}")

    print("[2/4] 🧩 jobs/lettering 합성 (검증된 운영값 적용)…")
    jobs, lettering = synth(beats, cast)
    json.dump(jobs, open(jobs_path, "w"), ensure_ascii=False, indent=1)
    json.dump(lettering, open(letter_path, "w"), ensure_ascii=False, indent=1)
    json.dump(beats, open(os.path.join(a.out, "beats.json"), "w"), ensure_ascii=False, indent=1)
    print(f"      {jobs_path}\n      {letter_path}")

    if a.skip_render:
        print("[3/4] ⏭  렌더 생략 (--skip-render)"); return
    print(f"[3/4] 🎨 패널 렌더 ({len(jobs)}컷, WeRU.B GPU)…")
    run([sys.executable, WERU_IMAGEGEN, "gen", "--jobs", jobs_path, "--out-dir", panels_dir])

    print("[4/4] 📜 세로 스크롤 뷰어 조립…")
    run([sys.executable, BUILD_VIEWER, "--panels-dir", panels_dir, "--lettering", letter_path,
         "--out", viewer_path, "--title", a.title, "--count", str(len(jobs))])
    print(f"\n✅ 완성 (Claude 미사용): {viewer_path}")


if __name__ == "__main__":
    main()
