#!/usr/bin/env python3
"""
weru_imagegen.py — WeRU.B GPU 이미지 서버용 배치 렌더 CLI (웹툰 하네스 로컬 백엔드).

codex CLI를 대체한다. 로컬 GPU 서버(WeRUBLLMManager)의 이미지 생성 API를
SSH 경유로 호출해 패널 PNG를 양산하고, 캐릭터 일관성(IP-Adapter)을 관리한다.

서버 접속(기본값, 환경변수로 덮어쓰기 가능):
  WERU_SSH=weruby@121.161.70.94   WERU_PORT=32200   WERU_API=http://127.0.0.1:8585
SSH는 무암호 키 인증이 설정돼 있어야 한다.

서브커맨드
  register  레퍼런스 이미지를 캐릭터로 등록 → character_id 반환 (일관성 SSOT)
  gen       잡 목록(JSON)을 큐에 일괄 등록 → 완료 폴링(백오프) → PNG 다운로드

잡 JSON 형식 (gen --jobs):
  [
    {"output":"panel_001.png",
     "prompt":"english prompt, NO speech bubble text baked",
     "model":"dreamshaper", "style":"illustration",
     "negative_prompt":"text, speech bubble, watermark, ...",
     "character_id":"<uuid>", "ip_adapter_mode":"full", "ip_adapter_strength":0.4,
     "width":832, "height":1216, "seed":1234},
    ...
  ]
  "output"은 다운로드 파일명(필수). 나머지는 API /api/image/generate 파라미터.

핵심 규약 (PoC로 검증된 값):
  - 작화 기본: model=dreamshaper, style=illustration (한국 웹툰 만화체)
  - 일관성: character_id + 샷별 IP-Adapter
      · 와이드/풀바디/액션 → ip_adapter_mode=full,  ip_adapter_strength=0.4
      · 감정 클로즈업       → ip_adapter_mode=face,  ip_adapter_strength=0.5
      · strength >= 0.6 금지 (구도·표정이 정면 상반신으로 붕괴)
  - 텍스트: 이미지에 한글/말풍선을 굽지 않는다. negative에 "text, speech bubble"을
    넣고 말풍선 자리만 비운다. 한글 대사는 조립 단계 HTML 오버레이가 얹는다.
  - 이미지엔 서버가 "AI 생성" 워터마크를 자동 삽입한다(제거 불가, 컴플라이언스).
"""
import argparse, json, os, subprocess, sys, tempfile, textwrap

SSH  = os.environ.get("WERU_SSH",  "weruby@121.161.70.94")
PORT = os.environ.get("WERU_PORT", "32200")
API  = os.environ.get("WERU_API",  "http://127.0.0.1:8585")

# 서버에서 실행되는 워커: stdin으로 {"jobs":[payload,...]} 받아 큐 등록→폴링(429 백오프)→
# "<idx>\t<status>\t<filename>" 출력. 서버 레이트리밋을 피하려고 가장 오래된 미완료 1건만
# 라운드로빈 폴링하고, 429에 지수 백오프한다.
WORKER = r'''
import sys, json, time, urllib.request, urllib.error
BASE = "%s"
def _req(path, data=None):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(data).encode() if data is not None else None,
        headers={"Content-Type": "application/json"} if data is not None else {})
    return json.loads(urllib.request.urlopen(req, timeout=25).read())
def call(path, data=None, tries=6):
    delay = 1.5
    for i in range(tries):
        try:
            return _req(path, data)
        except urllib.error.HTTPError as e:
            if e.code == 429 and i < tries - 1:
                time.sleep(delay); delay = min(delay * 2, 20); continue
            raise
req = json.loads(sys.stdin.read())
jobs = req["jobs"]
ids = [call("/api/image/generate", p).get("job_id") for p in jobs]
results = [None] * len(ids)
deadline = time.time() + 30 * 60
i = 0
while time.time() < deadline and any(r is None for r in results):
    if results[i] is None and ids[i]:
        s = call("/api/image/status/%%s" %% ids[i])
        st = s.get("status")
        if st == "completed":
            fn = (s.get("images") or [{}])[0].get("filename", "")
            results[i] = ("completed", fn)
        elif st == "failed":
            results[i] = ("failed", str(s.get("error")))
    if all(r is not None for r in results):
        break
    i = (i + 1) %% len(ids)
    if i == 0:
        time.sleep(2)
for k, r in enumerate(results):
    if r is None:
        r = ("timeout", "")
    print("%%d\t%%s\t%%s" %% (k, r[0], r[1]))
''' % API


def ssh(remote_cmd, input_bytes=None, capture=True):
    cmd = ["ssh", "-p", PORT, SSH, remote_cmd]
    return subprocess.run(cmd, input=input_bytes,
                          capture_output=capture, check=False)


def scp_to(local, remote):
    cmd = ["scp", "-P", PORT, local, f"{SSH}:{remote}"]
    return subprocess.run(cmd, capture_output=True, check=False)


def download(filename, dest):
    """/api/image/view는 presigned S3로 302 → curl -L 필수."""
    r = ssh(f"curl -sL {API}/api/image/view/{filename}", capture=True)
    with open(dest, "wb") as f:
        f.write(r.stdout)
    # PNG 시그니처 확인
    return r.stdout[:8] == b"\x89PNG\r\n\x1a\n"


def cmd_register(args):
    remote = f"/tmp/weru_char_{os.path.basename(args.image)}"
    if scp_to(args.image, remote).returncode != 0:
        sys.exit("ERROR: scp 실패 (레퍼런스 이미지 업로드)")
    tags = f'-F "tags={args.tags}"' if args.tags else ""
    r = ssh(f'curl -s -X POST {API}/api/image/character/create '
            f'-F "image=@{remote}" -F "name={args.name}" {tags}')
    out = r.stdout.decode(errors="replace").strip()
    print(out)
    try:
        cid = json.loads(out).get("character_id")
        if cid:
            sys.stderr.write(f"\ncharacter_id = {cid}\n")
    except Exception:
        sys.exit("ERROR: character/create 응답 파싱 실패")


def cmd_gen(args):
    jobs = json.load(open(args.jobs))
    if isinstance(jobs, dict):
        jobs = jobs.get("jobs", [])
    outputs = [j.get("output") for j in jobs]
    if any(not o for o in outputs):
        sys.exit("ERROR: 모든 잡에 'output' 파일명이 필요합니다.")
    # 하네스 메타 필드는 API로 보내지 않는다(서버는 무시하지만 방어적으로 제거).
    # 나머지는 모두 /api/image/generate 파라미터로 전달.
    META = {"output", "scene_group", "shot", "character_ids", "notes", "panel_id"}
    payloads = [{k: v for k, v in j.items() if k not in META} for j in jobs]

    os.makedirs(args.out_dir, exist_ok=True)
    # 워커 업로드 (idempotent)
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tf:
        tf.write(WORKER)
        worker_path = tf.name
    if scp_to(worker_path, "/tmp/weru_gen.py").returncode != 0:
        sys.exit("ERROR: 워커 업로드 실패")

    payload = json.dumps({"jobs": payloads}).encode()
    r = ssh("python3 /tmp/weru_gen.py", input_bytes=payload)
    lines = r.stdout.decode(errors="replace").strip().splitlines()
    if not lines:
        sys.exit("ERROR: 워커 무응답\n" + r.stderr.decode(errors="replace"))

    report = []
    for line in lines:
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        idx, status, filename = int(parts[0]), parts[1], parts[2]
        out_name = outputs[idx]
        dest = os.path.join(args.out_dir, out_name)
        ok = False
        if status == "completed" and filename:
            ok = download(filename, dest)
            status = "downloaded" if ok else "download_failed"
        report.append((out_name, status, filename))
        print(f"{out_name}\t{status}\t{filename}")

    bad = [r for r in report if r[1] != "downloaded"]
    if bad:
        sys.stderr.write(f"\n경고: {len(bad)}개 잡 실패 → 재렌더 필요: "
                         + ", ".join(b[0] for b in bad) + "\n")
        sys.exit(2)


def main():
    p = argparse.ArgumentParser(
        description="WeRU.B 이미지 서버 배치 렌더 CLI (웹툰 하네스 로컬 백엔드)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            예시:
              # 캐릭터 등록 (레퍼런스 → character_id)
              weru_imagegen.py register --image refs/jiho_ref.png --name jiho --tags webtoon,protagonist

              # 패널 배치 렌더 (jobs.json → _workspace/05_panels/ep01/*.png)
              weru_imagegen.py gen --jobs ep01_jobs.json --out-dir _workspace/05_panels/ep01
        """))
    sub = p.add_subparsers(dest="cmd", required=True)

    pr = sub.add_parser("register", help="레퍼런스 이미지를 캐릭터로 등록")
    pr.add_argument("--image", required=True)
    pr.add_argument("--name", required=True)
    pr.add_argument("--tags", default="")
    pr.set_defaults(func=cmd_register)

    pg = sub.add_parser("gen", help="잡 목록 배치 렌더 + 다운로드")
    pg.add_argument("--jobs", required=True, help="잡 JSON 파일 경로")
    pg.add_argument("--out-dir", required=True, help="PNG 저장 디렉토리")
    pg.set_defaults(func=cmd_gen)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
