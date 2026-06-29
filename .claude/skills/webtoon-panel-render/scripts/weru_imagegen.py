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

# 서버 워커 — argv 모드로 동작(짧은 연결로 분리해 장시간 SSH 연결 끊김을 회피).
#   submit : stdin {"jobs":[payload,...]} → 각 job_id 한 줄씩 출력 (빠름, <10s)
#   status : stdin {"ids":[id,...]}       → "<id>\t<status>\t<filename>" 한 줄씩 (1패스)
# 둘 다 429에 지수 백오프. 폴링 루프는 Mac 측에서 짧은 status 호출을 반복해 돈다.
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
mode = sys.argv[1]
data = json.loads(sys.stdin.read())
if mode == "submit":
    for p in data["jobs"]:
        try:
            print(call("/api/image/generate", p).get("job_id", ""))
        except Exception as e:
            print("")  # 빈 줄 = 제출 실패
elif mode == "status":
    for jid in data["ids"]:
        if not jid:
            print("\tfailed\t"); continue
        try:
            s = call("/api/image/status/%%s" %% jid)
            st = s.get("status")
            fn = (s.get("images") or [{}])[0].get("filename", "") if st == "completed" else ""
            print("%%s\t%%s\t%%s" %% (jid, st, fn))
        except Exception:
            print("%%s\terror\t" %% jid)
''' % API


def ssh(remote_cmd, input_bytes=None, capture=True):
    # 짧은 연결만 사용하되, NAT/유휴 끊김 방지를 위해 keepalive 옵션을 둔다.
    cmd = ["ssh", "-p", PORT,
           "-o", "ServerAliveInterval=15", "-o", "ServerAliveCountMax=8",
           "-o", "TCPKeepAlive=yes", SSH, remote_cmd]
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

    # 1) 제출 (짧은 연결) → job_id 목록
    r = ssh("python3 /tmp/weru_gen.py submit",
            input_bytes=json.dumps({"jobs": payloads}).encode())
    ids = r.stdout.decode(errors="replace").strip("\n").split("\n")
    if not ids or all(not i for i in ids):
        sys.exit("ERROR: 잡 제출 실패\n" + r.stderr.decode(errors="replace"))
    if len(ids) != len(outputs):
        sys.exit(f"ERROR: 제출 수({len(ids)}) != 잡 수({len(outputs)})")
    # job_id를 로컬에 저장(연결 끊겨도 복구 가능)
    with open(os.path.join(args.out_dir, ".jobids.json"), "w") as f:
        json.dump(dict(zip(outputs, ids)), f, ensure_ascii=False, indent=2)
    print(f"제출 완료: {sum(bool(i) for i in ids)}/{len(ids)} → 폴링 시작", file=sys.stderr)

    # 2) 폴링 (짧은 status 호출 반복 — 연결을 길게 잡지 않음)
    settled = {}  # idx -> (status, filename)
    import time as _t
    for round_no in range(240):  # 최대 ~12분
        pending = [i for i in range(len(ids)) if i not in settled and ids[i]]
        for i in range(len(ids)):
            if i not in settled and not ids[i]:
                settled[i] = ("failed", "")  # 제출 실패분
        if not pending:
            break
        rs = ssh("python3 /tmp/weru_gen.py status",
                 input_bytes=json.dumps({"ids": [ids[i] for i in pending]}).encode())
        for line, i in zip(rs.stdout.decode(errors="replace").strip("\n").split("\n"), pending):
            parts = line.split("\t")
            if len(parts) != 3:
                continue
            _, st, fn = parts
            if st == "completed":
                settled[i] = ("completed", fn)
            elif st in ("failed", "error"):
                settled[i] = ("failed", fn)
        if len(settled) >= len(ids):
            break
        _t.sleep(3)

    # 3) 다운로드 + 리포트
    report = []
    for i in range(len(ids)):
        st, fn = settled.get(i, ("timeout", ""))
        out_name = outputs[i]
        if st == "completed" and fn:
            ok = download(fn, os.path.join(args.out_dir, out_name))
            st = "downloaded" if ok else "download_failed"
        report.append((out_name, st, fn))
        print(f"{out_name}\t{st}\t{fn}")

    bad = [x for x in report if x[1] != "downloaded"]
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
