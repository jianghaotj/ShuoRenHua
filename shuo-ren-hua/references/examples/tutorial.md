# 教程示例

以下均为构造教学示例，界面和命令仅为例中约定。只选当前任务需要的 1—2 组。规范定义见 T01、F01/F03。

## U01 保留步骤与提示性冒号

- task: 根据给定材料写导出教程。
- audience: 第一次使用该界面的用户。
- operation: compose。
- source_facts: 用户须先打开报告页，再点击“导出”；点击后下载 CSV 文件；例中界面只支持导出当前页。
- must_preserve: 报告页、导出按钮、操作顺序、CSV 格式、当前页范围；没有全量导出能力。
- bad_transform: “点一下就能导出全部数据。”
- acceptable_outputs:

  > 导出当前页的数据：
  > 1. 打开报告页。
  > 2. 点击“导出”，下载 CSV 文件。
  >
  > 这里只导出当前页。

- why: 步骤、冒号和范围提示有实际作用；口语化不能掩盖操作前提或扩张功能。

## U02 代码保护与解释各司其职

- task: 为给定命令补一句说明，并原样保留命令。
- audience: 已了解工作目录的使用者。
- operation: explain_rewrite。
- source_facts: 例中命令 `tool export --format csv` 用于导出 CSV；用户要求这段命令逐字保留；未提供速度或安全性信息。
- must_preserve: `tool export --format csv` 的全部字符；CSV 导出用途。
- bad_transform: 把命令改成 `tool export --format excel`，并称它“能够安全快速地导出全部数据”。
- acceptable_outputs: “运行 `tool export --format csv`，导出 CSV 文件。”
- why: 自然语言可补用途，机器字段与显式保护片段不为通俗化改动，也不补未经支持的保证。
