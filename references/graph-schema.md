# Multi-level graph JSON schema

Create the complete visible ownership graph before running the renderer. `id` values must be unique. An edge always means `from` directly owns a stake in `to`. Repeated visual instances of the same subject intentionally use different `id` values and the same `entity_key`.

```json
{
  "title": "股权穿透图谱",
  "nodes": [
    {"id": "person_a_branch_1", "entity_key": "person_a", "label": "张某", "tag": "实际控制人\n受益所有人 65.02%", "shape": "ellipse", "style": "person", "level": 0, "order": 0},
    {"id": "person_b_branch_1", "entity_key": "person_b", "label": "胡某", "shape": "ellipse", "style": "person", "level": 0, "order": 1},
    {"id": "platform_1", "label": "员工持股平台（有限合伙）", "style": "company", "level": 1, "order": 0},
    {"id": "investor_2", "label": "外部投资合伙企业（有限合伙）", "style": "company", "collapsed": true, "level": 1, "order": 1},
    {"id": "target", "label": "目标公司", "style": "target", "level": 2, "order": 0}
  ],
  "edges": [
    {"from": "person_a_branch_1", "to": "platform_1", "holding": "99.99%"},
    {"from": "person_b_branch_1", "to": "platform_1", "holding": "0.01%"},
    {"from": "platform_1", "to": "target", "holding": "60%"},
    {"from": "investor_2", "to": "target", "holding": "40%"}
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
| `nodes[].entity_key` | no | Logical subject identifier shared by repeated visual instances of the same person/entity. |
| `nodes[].tag` | no | Editable label above a node, such as `GP`, `LP`, or an actual-controller badge. |
| `nodes[].level` | no | Top-down level, with `0` at the top. Use only to override auto-layout. |
| `nodes[].order` | no | Left-to-right position among nodes on the same level. |
| `nodes[].shape` | no | `rect` (default) or `ellipse`. |
| `nodes[].style` | no | `company` (default), `person`, or `target`. Styles remain native editable shapes. |
| `nodes[].collapsed` | no | `true` only when the PDF visibly shows a collapsed `+` upstream marker. |
| `edges[].from` / `to` | yes | Direct holder and direct investee ids. |
| `edges[].holding` | no | Percentage or other editable relationship label, e.g. `40%` or `认缴 100 万元`. |
| `edges[].confidence` | no | `high`, `medium`, or `low`; only for evidence review, not rendered. |
| `notes` | no | Unresolved reading issues that must be called out before delivery. |

## Completeness rules

- Preserve every visible ownership level. A graph that contains only direct shareholders when upstream branches are visible is invalid for delivery.
- Preserve repeated branch drawings. If 张某 appears above four separate platforms, create four display nodes such as `zhang_branch_1` through `zhang_branch_4`, all with `entity_key: "zhang"`.
- Keep every visible percentage on the exact direct edge shown in the PDF.
- A visible `+` means the source has hidden/collapsed upstream data. Set `collapsed: true`; do not invent the hidden nodes.
- Do not encode actual-controller or ultimate-beneficial-owner badges as ownership edges unless the PDF explicitly provides a direct holding relationship.
