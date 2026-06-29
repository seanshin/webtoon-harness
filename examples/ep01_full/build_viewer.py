#!/usr/bin/env python3
"""episode-compositor 참조 구현 — 텍스트 없는 패널 PNG + lettering.json 오버레이 → 세로 스크롤 index.html.

art-director style-bible '말풍선 오버레이 규약'을 CSS로 구현한다. 패널 PNG를 base64 data URI로
임베드해 어디서 열어도(이동·공유해도) 안 깨지는 자가완결 HTML을 만든다.

lettering.json 포맷: { "panel_001.png": [ [type, speaker, text, top, left, tail, max_width], ... ], ... }
  - type   : speech | thought | shout | narration | sfx
  - top/left/max_width : CSS 퍼센트 문자열(예 "6%", "52%") — 패널 박스 좌상단 기준
  - tail   : bottom-left | bottom-right | none

사용:
  python3 build_viewer.py \
      --panels-dir ../../_workspace/05_panels/ep01_full \
      --lettering  ../../_workspace/04_visual/ep01full_lettering.json \
      --out index_full.html --title "심야 편의점 — 1화" --count 70
"""
import argparse, base64, html, json, os, sys

CSS = """
:root { --w: 720px; }
* { box-sizing: border-box; }
body { margin:0; background:#0d0d0f; font-family:"Apple SD Gothic Neo","Noto Sans KR",sans-serif; }
.title { width:var(--w); max-width:100%; margin:0 auto; color:#eee; padding:18px 10px; font-size:20px; font-weight:800; }
.viewer { width:var(--w); max-width:100%; margin:0 auto; background:#000; }
.panel { position:relative; line-height:0; }
.panel img { width:100%; height:auto; display:block; }
.bubble { position:absolute; line-height:1.34; color:#111; font-size:19px; font-weight:600;
          background:#fff; border:2px solid #111; border-radius:20px; padding:11px 15px;
          box-shadow:0 3px 9px rgba(0,0,0,.35); }
.bubble::after { content:""; position:absolute; width:0; height:0; border:10px solid transparent; }
.tail-bottom-left::after  { border-top-color:#fff; bottom:-18px; left:24px; }
.tail-bottom-right::after { border-top-color:#fff; bottom:-18px; right:24px; }
.thought { border-style:dashed; border-radius:26px; background:rgba(255,255,255,.96); }
.thought::after { display:none; }
.shout { font-weight:800; font-style:italic; border-width:3px; font-size:23px; transform:rotate(-3deg); }
.narration { background:rgba(18,18,24,.92); color:#fff; border:none; border-radius:8px;
             font-weight:700; letter-spacing:.4px; text-align:center; }
.narration::after { display:none; }
.sfx { background:none; border:none; box-shadow:none; color:#fff; font-weight:800; font-style:italic;
       font-size:26px; text-shadow:0 2px 6px #000, 0 0 2px #000; padding:0; }
.sfx::after { display:none; }
"""


def img_data_uri(path):
    with open(path, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode("ascii")


def bubble_div(b):
    typ, speaker, text, top, left, tail, mw = b
    cls = f"bubble {typ}"
    if tail and tail != "none":
        cls += f" tail-{tail}"
    style = f"left:{left}; top:{top}; max-width:{mw};"
    return f'<div class="{cls}" style="{style}">{html.escape(text)}</div>'


def main():
    ap = argparse.ArgumentParser(description="텍스트 없는 패널 + lettering.json → 세로 스크롤 자가완결 index.html")
    ap.add_argument("--panels-dir", required=True, help="panel_NNN.png 들이 있는 디렉토리")
    ap.add_argument("--lettering", required=True, help="lettering.json 경로")
    ap.add_argument("--out", default="index.html", help="출력 HTML 경로")
    ap.add_argument("--title", default="웹툰", help="상단 타이틀")
    ap.add_argument("--count", type=int, required=True, help="패널 수(panel_001 ~ panel_{count})")
    a = ap.parse_args()

    lettering = json.load(open(a.lettering, encoding="utf-8"))
    order = [f"panel_{i:03d}.png" for i in range(1, a.count + 1)]
    parts = ['<!doctype html><html lang="ko"><head><meta charset="utf-8">',
             '<meta name="viewport" content="width=device-width, initial-scale=1">',
             f"<title>{html.escape(a.title)}</title><style>{CSS}</style></head><body>",
             f'<div class="title">{html.escape(a.title)}</div>', '<div class="viewer">']
    missing = []
    for fn in order:
        p = os.path.join(a.panels_dir, fn)
        if not os.path.exists(p) or os.path.getsize(p) == 0:
            missing.append(fn)
            parts.append(f'<div class="panel" style="height:300px;background:#222;color:#888;'
                         f'display:flex;align-items:center;justify-content:center;line-height:1">[{fn} 결손]</div>')
            continue
        bubs = "".join(bubble_div(b) for b in lettering.get(fn, []))
        parts.append(f'<div class="panel"><img src="{img_data_uri(p)}" alt="{fn}">{bubs}</div>')
    parts.append("</div></body></html>")
    open(a.out, "w", encoding="utf-8").write("\n".join(parts))
    print(f"wrote {a.out} ({len(order)} panels, missing={len(missing)}: {missing})")
    if missing:
        sys.exit(1)


if __name__ == "__main__":
    main()
