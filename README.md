# 说人话 · ShuoRenHua

> 保留事实和原意，把中文写清楚，让表达符合读者和场合。

![说人话：把意思讲清楚，把原意留下来](assets/shuorenhua-cover.png)

[![Version](https://img.shields.io/badge/version-1.1.0-1f1a14)](CHANGELOG.md)
[![License: MIT](https://img.shields.io/badge/license-MIT-8f7650)](LICENSE)
[![skills.sh 安装统计](https://skills.sh/b/jianghaotj/ShuoRenHua)](https://skills.sh/jianghaotj/ShuoRenHua)

「说人话」是给 AI Agent 使用的中文写作与改稿技能，适用于日常沟通、工作消息、解释、摘要、分析、教程和叙事创作。

你可以交给它一段需要润色的文字，也可以提供材料，请它从头起草。只说“润色”时，默认轻改；原文已经合适，就保留。

## 它能做什么

| 你要做的事 | 它会重点处理什么 |
| --- | --- |
| 润色一段文字 | 修正不顺的表达，保留原意、语气和必要限定 |
| 写工作消息或邮件 | 说清对象、行动、责任和已有的时间要求 |
| 解释一个概念 | 按读者已有的知识解释术语，把关系讲明白 |
| 整理摘要 | 提取核心信息，保留影响结论的条件和范围 |
| 写分析 | 说清结论的条件、依据和代价 |
| 写教程 | 按操作顺序安排步骤，在对应位置说明前提、结果和风险 |
| 写长文、故事或对白 | 保留叙述声音、人物视角和节奏，区分现实材料与虚构内容 |

改稿时，它会核对容易被改丢的信息，例如时间、数字、否定、条件、责任和承诺。

“尚未发现问题”不能改成“没有问题”；“可能有效”不能改成“明确有效”。文字更顺的同时，意思也应当准确。

1.1.0 补充了教程的步骤顺序、备注和警告写法，也细化了用词与重复表述的审校规则。版本改动见 [更新记录](CHANGELOG.md)。

<p align="center">
  <img src="assets/shuorenhua-principles.png" alt="该改的地方改，写得好的地方留：默认轻改、保留条件与承诺、按读者和场合表达、检查结果供审校参考" width="540">
</p>

## 安装

把下面这段话发给支持安装技能的 AI Agent：

```text
帮我安装「说人话」技能：
https://github.com/jianghaotj/ShuoRenHua

请安装仓库中的 shuo-ren-hua 文件夹，并保留其中的参考文件、脚本和许可证。
```

如果已安装 Node.js 和 npm，可以用 [skills CLI](https://github.com/vercel-labs/skills#install-a-skill) 安装：

```bash
npx skills add jianghaotj/ShuoRenHua --skill shuo-ren-hua
```

按提示选择要使用的工具，以及安装到当前项目还是用户目录。

如果你的工具不支持直接安装，可以下载仓库，将完整的 `shuo-ren-hua` 文件夹放入该工具的 Skills 目录。具体位置以工具的安装说明为准。

## 使用

在 Codex 输入框中输入 `/`，搜索并选择中文显示名「说人话」，再填写需求。其他工具的选择入口以该工具的说明为准。

也可以在提示词中说明要使用说人话技能：

```text
使用说人话技能，轻度润色下面这段话。
保留事实、原意和语气，只修改不顺的地方。
```

```text
使用说人话技能，把这些材料整理成一条发给同事的工作消息。
说清当前进展、需要对方处理的事项和已有截止时间。
```

```text
使用说人话技能，向第一次接触这个概念的人解释它。
必要术语可以保留，但要讲清楚含义。
```

<details>
<summary>安装统计与隐私</summary>

顶部的安装量徽章来自 skills.sh，只反映其安装入口收集到的统计，不代表全部安装人数；手动复制等安装方式不计入。

skills CLI 的匿名使用统计可以关闭，方法见其 [遥测说明](https://github.com/vercel-labs/skills#telemetry)。说人话技能本身不含收集写作内容或调用次数的统计代码。

</details>

## 相比「活人感写作」，调整了什么

对照上游 [1.1.0 技能规则](https://github.com/KKKKhazix/human-writing/blob/4fda173f3fef7fb808f3eba991eeb2528ea4b189/human-writing/SKILL.md)，本项目主要做了以下调整：

| 方面 | 本项目的调整 |
| --- | --- |
| 默认写法 | 根据任务、读者和场合选择结构；需要长帖时再使用长帖写法 |
| 润色范围 | 明确区分轻改、重写、解释性改写和摘要；只说润色时默认轻改 |
| 信息保留 | 核对数字、条件、否定、范围、结论强度、责任、承诺和引用，避免改稿时改变原意 |
| 风格判断 | 允许必要的冒号、对比句和专业词，根据上下文判断是否影响理解 |
| 材料不足 | 判断缺失信息是否会改变事实、承诺或核心选择，再决定补充、询问或缩小写作范围，不以固定材料数量作为开稿门槛 |
| 审校流程 | 短消息直接写作或局部修改；长文集中修订，必要时再修复已定位的问题 |
| 检查工具 | 区分风格提醒、精确保留检查与无法自动判断的语义问题 |

实际输出仍取决于模型、材料和提示要求。

## 可选的本地检查

需要审校长文时，可以使用技能附带的本地文字检查器。在 `shuo-ren-hua` 目录中检查 `article.md`：

```bash
python3 scripts/check_prose.py article.md --profile professional --format json
```

检查器只读、不联网、不调用模型，也不自动改稿。

它会标出可能需要修改的表达，供你结合上下文判断。提供原稿和逐字保留契约后，还能检查指定文字是否原样保留。契约的格式和调用方法见 [忠实改写与修改范围](shuo-ren-hua/references/editing.md#可选保真契约)。

事实真假、引用是否支持结论，以及改写是否完整保留原意，仍需结合上下文审查。检查器没有报错，不等于文章可以直接发布。

日常短消息和轻度润色不需要运行检查器。

## 仓库结构

```text
ShuoRenHua/
├── README.md
├── LICENSE
├── CHANGELOG.md
├── assets/
└── shuo-ren-hua/
    ├── SKILL.md
    ├── LICENSE
    ├── agents/
    ├── references/
    │   ├── editing.md
    │   ├── plain-language.md
    │   ├── reality.md
    │   ├── formats.md
    │   ├── forum-prose.md
    │   ├── fiction.md
    │   ├── revision.md
    │   ├── rules.json
    │   └── examples/
    └── scripts/
        ├── check_prose.py
        ├── check_contract.py
        └── prose_blocks.py
```

`SKILL.md` 是技能入口；`references/` 提供按需读取的规则和示例；`scripts/` 提供可选检查工具。

## 问题反馈

遇到改写失真、过度润色、规则冲突或检查器误报，欢迎 [提交 Issue](https://github.com/jianghaotj/ShuoRenHua/issues)。

为了复现问题，请尽量提供：

- 使用的工具、模型和技能版本。
- 提示词与必要的原文片段。
- 实际输出，以及你希望保留或调整的内容。
- 如果涉及检查器，附上命令和相关报告。

提交前请移除个人隐私和公司内部信息。

## 参考

1.1.0 在已有规则上，按中文写作场景筛选了以下资料中的写法：

- [lieflat-less-ai-tone](https://github.com/larashero3-dotcom/lieflat-less-ai-tone)（MIT）：部分表达的触发形态及检查器词表，保留作者版权声明。
- [Google developer documentation style guide](https://developers.google.com/style)（CC BY 4.0）：信息顺序、教程步骤、备注与警告、术语和产品能力的表达。
- [ASD-STE100 Issue 9](https://asd-ste100.org/)（© ASD）：词义、指代和操作说明的写法。标准原始文件不随仓库分发。

具体对应的页面、规则与适用范围见 [formats.md](shuo-ren-hua/references/formats.md) 和 [plain-language.md](shuo-ren-hua/references/plain-language.md)。例句采用自拟的中文场景；本技能不是上述标准的实现、译本或认证产物。

## 致谢与许可

本项目基于 [KKKKhazix/human-writing](https://github.com/KKKKhazix/human-writing) 改进，感谢上游作者与贡献者。

技能规则、文档和脚本采用 [MIT 许可证](LICENSE)，保留上游版权与许可声明。第三方素材如有单独许可，以对应说明为准。

卡片使用 [Guizang Social Card Skill](https://github.com/op7418/guizang-social-card-skill) 制作，制作工具采用 AGPL-3.0，未作为技能依赖分发。图片的制作来源见 [assets/SOURCES.md](assets/SOURCES.md)。

「说人话」用于改善表达，不用于规避 AI 检测或伪造真人经历。
