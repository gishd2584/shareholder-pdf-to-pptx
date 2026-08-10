# Shareholder PDF to editable PPTX

把股权穿透 PDF（包括没有文本层的长截图 PDF）完整重建为多级、原生可编辑的 PowerPoint 图谱。节点、公司全称、比例、实控人标签、折叠标记和连接线都可以在 PowerPoint 中单独修改。

## 一句话安装

```bash
npx skills add gishd2584/shareholder-pdf-to-pptx -g -y
```

安装后可直接对 Agent 说：

> 使用 $shareholder-pdf-to-pptx，把这个股权穿透 PDF 完整转换成多级可编辑 PPT；保留所有可见层级、重复分支主体、比例和折叠标记。

## 特点

- 纯 Python：PDF 提取、图谱校验、PPTX 生成和预览脚本全部包含在 Skill 内。
- 完整多级：不会把已经展开的上游穿透关系压平为一级股东。
- 原生可编辑：使用 PowerPoint 形状、文本框、线条、总线和连接箭头，不粘贴整页图片。
- 分支保真：同一主体在不同分支中可以保留多个显示节点，并通过 `entity_key` 关联。
- 不虚构数据：源图的 `+` 作为折叠标记保留，不猜测未展开的隐藏股东。

运行环境和标准流程见 [SKILL.md](SKILL.md)，图谱数据格式见 [references/graph-schema.md](references/graph-schema.md)。
