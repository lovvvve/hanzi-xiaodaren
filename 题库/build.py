#!/usr/bin/env python3
"""合并分片 + 生成 index.json + 导出 all.jsonl。

- 真题/_parts/<set_id>.partN.json 按 N 顺序合并为 真题/<set_id>.json
- 扫描 真题/、模拟/ 下所有套卷，生成 index.json（各套题数、题型分布、flag 统计）
- all.jsonl：每行一题，附带 set_id / group / level / year，便于检索或导入
- 待核对.md：answer_doubt / text_uncertain / answer_by_ai 题目清单
"""
import collections
import glob
import json
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
GROUPS = ["真题", "模拟"]


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def dump(obj, p):
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def merge_parts():
    by_set = collections.defaultdict(list)
    for p in glob.glob(os.path.join(ROOT, "*", "_parts", "*.part*.json")):
        m = re.match(r"(.+)\.part(\d+)\.json$", os.path.basename(p))
        by_set[(os.path.dirname(os.path.dirname(p)), m.group(1))].append((int(m.group(2)), p))
    for (gdir, sid), parts in by_set.items():
        parts.sort()
        docs = [load(p) for _, p in parts]
        base = dict(docs[0])
        secs = {}
        for d in docs:
            for s in d["sections"]:
                secs.setdefault(s["no"], s)
        base["sections"] = [secs[k] for k in sorted(secs)]
        base["questions"] = [q for d in docs for q in d["questions"]]
        # 分片来源（市赛线上卷）各代理对 no 口径不一，统一为大题内序号
        pos = collections.Counter()
        for q in base["questions"]:
            pos[q["section"]] += 1
            q["no"] = pos[q["section"]]
        base["sources"] = list(dict.fromkeys(s for d in docs for s in d["sources"]))
        out = os.path.join(gdir, f"{sid}.json")
        dump(base, out)
        print(f"合并 {len(parts)} 个分片 -> {os.path.relpath(out, ROOT)} ({len(base['questions'])} 题)")


def build_index():
    sets, lines = [], []
    for g in GROUPS:
        for p in sorted(glob.glob(os.path.join(ROOT, g, "*.json"))):
            d = load(p)
            qs = d["questions"]
            flags = collections.Counter(f for q in qs for f in q["flags"])
            sets.append({
                "id": d["id"], "title": d["title"], "group": d["group"], "level": d["level"],
                "year": d["year"], "date": d["date"], "file": os.path.relpath(p, ROOT),
                "count": len(qs),
                "sections": [{"no": s["no"], "title": s["title"], "type": s["type"],
                              "count": sum(q["section"] == s["no"] for q in qs)} for s in d["sections"]],
                "types": dict(collections.Counter(q["type"] for q in qs).most_common()),
                "flags": dict(flags.most_common()),
            })
            for q in qs:
                lines.append(json.dumps({"set_id": d["id"], "group": d["group"], "level": d["level"],
                                         "year": d["year"], **q}, ensure_ascii=False))
    idx = {
        "total": sum(s["count"] for s in sets),
        "by_group": {g: sum(s["count"] for s in sets if s["group"] == g) for g in GROUPS},
        "sets": sets,
    }
    dump(idx, os.path.join(ROOT, "index.json"))
    with open(os.path.join(ROOT, "all.jsonl"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"index.json: {len(sets)} 套, 共 {idx['total']} 题 {idx['by_group']}")


REVIEW_FLAGS = ["answer_doubt", "answer_by_ai", "text_uncertain"]


def build_review():
    out = ["# 待核对题目", "", "由 build.py 生成，勿手改。修正 JSON 后重新运行 `python3 build.py`。", ""]
    for g in GROUPS:
        for p in sorted(glob.glob(os.path.join(ROOT, g, "*.json"))):
            d = load(p)
            hit = [q for q in d["questions"] if set(q["flags"]) & set(REVIEW_FLAGS)]
            if not hit:
                continue
            out += [f"## {d['id']}　{d['title']}（{len(hit)} 题）", "",
                    "| id | 页 | flag | 题干 | 原答案 | 备注 |", "|---|---|---|---|---|---|"]
            for q in hit:
                cell = lambda x: str(x if x is not None else "").replace("|", "\\|").replace("\n", " ")
                fl = ",".join(f for f in q["flags"] if f in REVIEW_FLAGS)
                out.append(f"| {q['id']} | {q['source_page'] or ''} | {fl} | {cell(q['stem'])[:40]} "
                           f"| {cell(q['answer'])} | {cell(q['note'])} |")
            out.append("")
    with open(os.path.join(ROOT, "待核对.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print("待核对.md 已生成")


if __name__ == "__main__":
    merge_parts()
    build_index()
    build_review()
