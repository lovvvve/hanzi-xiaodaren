#!/usr/bin/env python3
"""生成真题答案说明页：答案以原始答案文件为准，只列答案文件本身需要说明的题。输出 题库/kancuo.html。"""
import json
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(os.path.dirname(ROOT), "data", "市赛真题")
KEY_FILE = os.path.join(DATA, "06 第七届汉字小达人市级比赛真题参考答案（同excel）.txt")
SID, SHORT = "zt-2020-shisai", "第七届市赛"
GROUPS = {"conflict": [75], "guess": list(range(106, 121))}


def doc_keys():
    txt = subprocess.run(["iconv", "-f", "gbk", "-t", "utf-8", KEY_FILE], capture_output=True, text=True).stdout
    out = {}
    for line in txt.splitlines():
        p = line.rstrip("\r").split("\t")
        if p[0].strip().isdigit():
            out[int(p[0])] = p[1].strip()
    return out


def main():
    d = json.load(open(os.path.join(ROOT, "真题", SID + ".json"), encoding="utf-8"))
    sec = {s["no"]: s["title"] for s in d["sections"]}
    keys = doc_keys()
    items = []
    for g, seqs in GROUPS.items():
        for q in d["questions"]:
            if q["seq"] not in seqs:
                continue
            m = re.match(r"^([一二三四五六七八九十]+)、", sec[q["section"]])
            items.append({"id": q["id"], "set": SID, "set_short": SHORT, "seq": q["seq"], "no": q["no"],
                          "sec": (m.group(1) + "·") if m else "", "page": q["source_page"], "type": q["type"],
                          "format": q["format"], "stem": q["stem"], "pinyin": q["pinyin"], "options": q["options"],
                          "images": q["images"], "key": q["answer"], "key_full": q["answer_full"],
                          "doc_text": f"第 {q['seq']} 题：{keys.get(q['seq'], '')}", "note": q["note"], "group": g})
    data = {"sets": [{"id": SID, "short": SHORT}], "items": items}
    js = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    tpl = open(os.path.join(ROOT, "web", "kancuo.tpl.html"), encoding="utf-8").read()
    out = os.path.join(ROOT, "kancuo.html")
    open(out, "w", encoding="utf-8").write(tpl.replace("__DATA__", js, 1))
    print(f"{out}: {len(items)} 题，图片 {len({i for x in items for i in x['images']})} 张")


if __name__ == "__main__":
    main()
