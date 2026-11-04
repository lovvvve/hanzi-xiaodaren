# 汉字小达人题库

源资料：`../data/`。题库分两组：

- `真题/`：历年真题（市赛、区赛）
- `模拟/`：杂志 7&8 月刊模拟题、官方模拟题

每套卷子一个 JSON 文件，文件名 = 套卷 id。`index.json` 是总索引。图片题的原页渲染图放在 `assets/<set_id>/`。

- `index.json`：总索引（每套题数、大题、题型分布、flag 统计）
- `all.jsonl`：全部题目扁平化，每行一题，附带 set_id / group / level / year
- `待核对.md`：答案存疑、识读不确定的题目清单

构建：`python3 build.py`（改完 JSON 后重跑，生成 index.json / all.jsonl / 待核对.md）
校验：`python3 validate.py 真题/*.json 模拟/*.json`

## 套卷 id

| id | 组 | 题数 | 说明 |
|---|---|---|---|
| zt-2020-shisai | 真题 | 150 | 第七届市级比赛（2020-11-19，线上 150 题） |
| zt-2021-shisai | 真题 | 150 | 第八届市级比赛（2021-11-25，线上 150 题） |
| zt-2025-qusai | 真题 | 105 | 2025 区赛 |
| mn-2022-0708 | 模拟 | 345 | 2022《聪明小豆丁》7&8 月刊模拟题 |
| mn-2023-0708 | 模拟 | 345 | 2023《聪明小豆丁》7&8 月刊模拟题 |
| mn-2025-official | 模拟 | 350 | 2025 官方模拟题 |
| mn-2026-0708 | 模拟 | 350 | 2026 7&8 月刊模拟题 |

## Schema

### 套卷（文件顶层）

```jsonc
{
  "id": "zt-2020-shisai",
  "title": "第七届汉字小达人市级比赛真题",
  "group": "真题",            // 真题 | 模拟
  "level": "市赛",            // 市赛 | 区赛 | 模拟
  "year": 2020,
  "date": "2020-11-19",       // 未知则 null
  "sources": ["data/市赛真题/05 第七届汉字小达人市级比赛真题.pdf"],  // 相对项目根
  "notes": "答题 40 分钟，每题 1 分",  // 可空
  "sections": [
    { "no": 1, "title": "一、请选择正确的选项，将下列词语填写完整。（每小题1分，共30题）", "type": "word_fill", "format": "choice" }
  ],
  "questions": [ /* 见下 */ ]
}
```

### 题目

```jsonc
{
  "id": "zt-2020-shisai-001",   // <set_id>-<seq 三位补零>
  "seq": 1,                      // 全卷顺序号，从 1 连续
  "section": 1,                  // 对应 sections[].no
  "no": 1,                       // 大题内序号（卷面印了就照印的；市赛线上卷按大题内顺序编）。全卷顺序看 seq
  "type": "word_fill",           // 知识类别，见下表
  "format": "choice",            // choice | fill | judge | link
  "stem": "他根本没听见周围___闹的声音，整个世界对他来说好像都消失了。",
  "pinyin": null,                // 题目给出的拼音（pinyin 类必填），带声调原样转写
  "options": [                   // 仅 choice；无字母的按显示顺序编 A/B/C/D
    { "key": "A", "text": "喧" }, { "key": "B", "text": "暄" }
  ],                             // 选项是非规范字时可加 "img": "assets/..."（该字的裁图），text 用〔部件+部件〕描述
  "answer": "A",                 // choice=选项 key；judge="√"/"×"；fill=所填内容；多空用数组按空位顺序
  "answer_full": "喧闹",          // 可选：完整词语/成语/诗句，便于展示
  "analysis": null,              // 解析（原资料有才填，或答案文件里的补充说明）
  "grade": null,                 // 区赛分层："4-5"=四五年级必做，"5"=五年级必做，"附加"=附加题；其余 null
  "images": [],                  // 题目依赖图片时填，路径相对 题库/，如 "assets/zt-2020-shisai/p112.png"
  "source_page": 5,              // 题目所在 PDF 页码（1 起）；docx/xlsx 来源可 null
  "flags": [],                   // 见下
  "note": null                   // 整理者备注（存疑原因等）
}
```

`stem` 里空位统一用 `___`（三个下划线），多空就多个 `___`。

### type 知识类别

| type | 含义 |
|---|---|
| pinyin | 看拼音写/选汉字 |
| word_fill | 选字/写字补全词语（同音、形近字辨析） |
| idiom_fill | 补全成语 |
| idiom_pick | 从给出的字中挑出四字成语 |
| idiom_from_text | 根据文言文/古诗词写出相关成语 |
| char_meaning | 根据字义选择 |
| glyph | 字形识字（甲骨文、金文、篆书等古文字） |
| poem_fill | 诗句填空/补全 |
| poem_link | 字格中找诗句并连线 |
| quote_context | 按情境写诗句、名言 |
| word_usage | 词语运用、错别字辨析、读音等语言知识综合题 |
| culture | 文学、国学、传统文化常识 |
| other | 以上都不是 |

判断题用 `format: "judge"`，`type` 按内容归类。

### flags

| flag | 含义 |
|---|---|
| answer_missing | 原资料无答案，且未能可靠给出 |
| answer_by_ai | 原资料无答案，由整理者推断填写 |
| answer_doubt | 原资料答案存疑（保留原答案，`note` 写明理由与建议答案） |
| text_uncertain | 题面识读不确定（扫描模糊等） |
| image_required | 题目离不开图片（文字无法完整表达） |
