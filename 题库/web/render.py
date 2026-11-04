#!/usr/bin/env python3
"""生成刷题页：python3 web/render.py [真题|模拟|合并]（缺省全部生成）

读 真题/*.json、模拟/*.json，内联进 web/zhenti.tpl.html：
- 真题 → 题库/zhenti.html，模拟 → 题库/moni.html（claude.ai Artifact 用，图片路径相对 题库/）
- 合并 → 仓库根目录 index.html（GitHub Pages 首页，图片路径加 “题库/” 前缀）
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEEP = ["id", "seq", "section", "no", "type", "format", "stem", "pinyin", "options", "answer",
        "answer_full", "analysis", "grade", "images", "flags", "note", "source_page"]
GROUPS = {
    "真题": {"id": "zt", "label": "全部真题",
             "sets": {"zt-2020-shisai": "第七届市赛", "zt-2021-shisai": "第八届市赛", "zt-2025-qusai": "2025 区赛"}},
    "模拟": {"id": "mn", "label": "全部模拟题",
             "sets": {"mn-2026-0708": "2026 模拟", "mn-2025-official": "2025 官方模拟", "mn-2023-0708": "2023 模拟",
                      "mn-2022-0708": "2022 模拟"}},
}
PLAY = "选择题点选项即判分；挑字成语、字格连诗句按顺序点字；其他填空题在田字格里手写，再看答案对照。答错的题自动收进错题本。"
SRC = "题目转写自原卷截图和扫描件，原卷上的错字照原样保留。答案一律以原始答案文件为准，每题都已与答案文件逐题核对；"
FIX = "个别卷面印错、答案文件写明了正确内容的选项和字格，已按答案文件修正，并在“整理备注”里注明。"
GUESS = "第七届市赛第 106–120 题（古文字），答案文件自己注明“基本是蒙的”。"
PAGES = {
    "真题": {"out": "zhenti.html", "groups": ["真题"], "title": "汉字小达人真题", "tail": "真题", "def": "g-zt", "prefix": "",
             "lede": "上海市小学生“汉字小达人”第七届、第八届市赛和 2025 区赛真题。" + PLAY,
             "foot": SRC + GUESS},
    "模拟": {"out": "moni.html", "groups": ["模拟"], "title": "汉字小达人模拟题", "tail": "模拟题", "def": "mn-2026-0708", "prefix": "",
             "lede": "上海市小学生“汉字小达人”模拟题：《聪明小豆丁》2022、2023、2026 年 7&8 月刊和 2025 官方模拟题。" + PLAY,
             "foot": SRC + FIX + "古文字题的字形从原卷单独裁出，点图可放大。"},
    "合并": {"out": "../index.html", "groups": ["真题", "模拟"], "title": "汉字小达人题库", "tail": "题库", "def": "g-zt",
             "prefix": "题库/",
             "lede": "上海市小学生“汉字小达人”历年真题（第七届、第八届市赛，2025 区赛）和模拟题（2022、2023、2026 年 7&8 月刊，"
                     "2025 官方模拟），共 1795 题。" + PLAY,
             "foot": SRC + FIX + GUESS + "资料版权归原出版方所有，本站仅供学习交流。", "standalone": True},
}


# 独立网站（GitHub Pages）用：补完整文档骨架（Artifact 发布时由平台自动包上），并去掉国内打不开的 Google Fonts
SKELETON = ('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
            '<style>:root{color-scheme:light;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}'
            'body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style></head><body>\n')


def standalone(html):
    lines = [l for l in html.split("\n") if "fonts.googleapis.com" not in l and "fonts.gstatic.com" not in l]
    return SKELETON + "\n".join(lines) + "\n</body></html>\n"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render(page):
    c = PAGES[page]
    pre = c["prefix"]
    groups, sets, qs = [], [], []
    for gname in c["groups"]:
        g = GROUPS[gname]
        groups.append({"id": g["id"], "label": g["label"]})
        for sid, short in g["sets"].items():
            with open(os.path.join(ROOT, gname, sid + ".json"), encoding="utf-8") as f:
                d = json.load(f)
            sets.append({"id": d["id"], "group": g["id"], "title": d["title"], "short": short, "year": d["year"],
                         "date": d["date"], "level": d["level"], "notes": d["notes"],
                         "sections": [{"no": s["no"], "title": s["title"]} for s in d["sections"]]})
            for q in d["questions"]:
                x = {"set": sid, **{k: q[k] for k in KEEP}}
                x["images"] = [pre + i for i in q["images"]]
                if q["options"]:
                    x["options"] = [{**o, "img": pre + o["img"]} if o.get("img") else o for o in q["options"]]
                qs.append(x)
    data = {"cfg": {"def": c["def"]}, "groups": groups, "sets": sets, "questions": qs}
    js = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    with open(os.path.join(ROOT, "web", "zhenti.tpl.html"), encoding="utf-8") as f:
        tpl = f.read()
    for k in ("title", "tail", "lede", "foot"):
        tpl = tpl.replace(f"__{k.upper()}__", esc(c[k]), 1)
    out = os.path.normpath(os.path.join(ROOT, c["out"]))
    html = tpl.replace("__DATA__", js, 1)
    if c.get("standalone"):
        html = standalone(html)
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    imgs = sorted({i[len(pre):] for q in qs for i in q["images"]} |
                  {o["img"][len(pre):] for q in qs for o in (q["options"] or []) if o.get("img")})
    print(f"{out}: {len(qs)} 题, {os.path.getsize(out) // 1024} KB, 引用图片 {len(imgs)} 张")
    return imgs


if __name__ == "__main__":
    for p in (sys.argv[1:] or list(PAGES)):
        render(p)
