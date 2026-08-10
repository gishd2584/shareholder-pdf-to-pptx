# Graph JSON schema

Create an ownership graph before running the renderer. `id` values must be unique. An edge always means `from` directly owns a stake in `to`.

```json
{
  "title": "代持还原后",
  "nodes": [
    {"id": "holder", "label": "原代持人", "tag": "GP", "level": 0, "order": 0},
    {"id": "lp", "label": "新LP", "tag": "LP", "level": 0, "order": 1},
    {"id": "platform", "label": "合伙平台", "level": 1},
    {"id": "jv", "label": "合资公司", "level": 2}
  ],
  "edges": [
    {"from": "holder", "to": "platform", "holding": "1.23%"},
    {"from": "lp", "to": "platform", "holding": "98.77%"},
    {"from": "platform", "to": "jv", "holding": "41%"}
  ],
  "notes": [
    "Only use this array for unresolved OCR or relationship ambiguity."
  ]
}
```

## Fields

| Field | Required | Meaning |
| --- | --- | --- |
| `title` | no | Displayed title; defaults to `股权架构图`. |
| `nodes[].id` | yes | Stable ASCII identifier referenced by edges. |
| `nodes[].label` | yes | Entity name shown in the box. Preserve original legal names. |
| `nodes[].tag` | no | Short editable label above a node, such as `GP`, `LP`, or `实控人`. |
| `nodes[].level` | no | Top-down level, with `0` at the top. Use only to override auto-layout. |
| `nodes[].order` | no | Left-to-right position among nodes on the same level. |
| `nodes[].shape` | no | `rect` (default) or `ellipse`. |
| `edges[].from` / `to` | yes | Direct holder and direct investee ids. |
| `edges[].holding` | no | Percentage or other editable relationship label, e.g. `40%` or `认缴 100 万元`. |
| `edges[].confidence` | no | `high`, `medium`, or `low`; only for evidence review, not rendered. |
| `notes` | no | Unresolved reading issues that must be called out before delivery. |

Do not encode ultimate-beneficial-owner labels as ownership edges unless the PDF explicitly provides a direct holding relationship.
