# 说人话 · ShuoRenHua

> 把晦涩难懂的文字、公文腔或 AI 味浓重的稿子，写成一眼能看懂、像真人说话的中文；同时死死守住事实、数据和原意底线。

![说人话：把意思讲清楚，把原意留下来](assets/shuorenhua-cover.png)

[![Version](https://img.shields.io/badge/version-2.0.0-1f1a14)](CHANGELOG.md)
[![License: MIT](https://img.shields.io/badge/license-MIT-8f7650)](LICENSE)
[![skills.sh 安装统计](https://skills.sh/b/jianghaotj/ShuoRenHua)](https://skills.sh/jianghaotj/ShuoRenHua)

「说人话」是给 AI Agent 使用的中文写作与改稿技能。

很多时候 AI 写出来的东西（或者我们自己赶出来的初稿）每个字都认识，连在一起却让人读得脑仁疼：到处是“赋能、抓手、闭环、颗粒度”，到处是塞了四五层定语的百字免责长句，或者端着一副滴水不漏却毫无温度的客服腔。

这个技能的核心任务，就是帮 AI **敲碎那层拧巴的硬壳，用真人的说话逻辑把事儿讲透**。

## 2.0 彻底重构了什么？

在 1.x 版本中，为了防止改丢信息，规则本身写得像法务条文和航空说明书，导致模型被上下文传染，改稿束手束脚。**2.0.0 做了一次彻底的“换魂”升级**：

1. **以身作则，规则本身 100% 说人话**：彻底清除了技能内部法条式、高密度的抽象指令，防止规则文档反向污染大模型的文风。
2. **从“保守微调”转向“破壳重说（保意不保壳）”**：当原稿晦涩、绕口或充满 AI 味时，不再束手束脚地换同义词，而是直接打碎原句壳子，按活人说话的顺序重讲一遍；只有原稿本身已经自然通顺时才做微调。
3. **提炼 6 把“去 AI 味 & 降理解门槛”的手术刀**：
   - 把“概念/抽象名词做主语”还原成“人或具体事物做主语 + 具体动作”；
   - 砍断“名词火车”与超长定语；
   - 把“百字免责长句”拆成“先痛快说事，再自然交代边界”；
   - 给陌生概念和绕弯逻辑“搭梯子”（允许用大白话复述、拿日常经验打比方）；
   - 撕掉 AI 的“四平八稳客服面具”、“假反转”、“段末强行升华”和“PPT 大纲强迫症”；
   - 顺着读者脑子里的“下一秒疑问”往前推，而不是按分类报菜名。
4. **重写全套前后对照范例库**：把原本单元测试式的干巴短句，全部替换为极具代表性的「❌ 典型 AI 腔/晦涩公文 vs ✅ 说人话改写版 + 💡 动刀解析」完整段落对照。

## 它能帮你干什么？

| 你手头的活儿 | 它会怎么处理 |
| --- | --- |
| **把难懂/AI 味重的话改成说人话** | 敲碎长定语和公文壳子，把抽象大词还原成具体动作，同时守住原有的数字、条件和分寸 |
| **向别人解释复杂概念** | 从对方已经懂的日常常识出发，一次只讲透一个新词，顺手打比方搭梯子 |
| **写工作消息或催办邮件** | 刮掉互联网黑话，前三句亮明：出了啥事、需要谁干啥、最晚几点前要 |
| **写分析汇报与建议** | 不做“端水大师”，亮出带前提的明确判断，替读者算清背后的成本、代价和风险 |
| **写操作教程与说明** | 一步只干一件事，“前提、位置、危险警告”写在动手前面，不用“只需、轻松”糊弄人 |
| **写公众号、知乎长文或故事** | 从具体痛点或冲突切入，用读者脑子里的下一个问题推着文章走，用扎手的细节代替塑料形容词 |
| **整理会议录音与访谈** | 删掉口头禅和车轱辘话，按主题理顺逻辑，留住发言人的限定语气，听不清的人名数字标待确认 |

<p align="center">
  <img src="assets/shuorenhua-principles.png" alt="该改的地方改，写得好的地方留：破壳重说、保留条件与承诺、按读者和场合表达" width="540">
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

如果你的工具不支持直接安装，直接把仓库里的 `shuo-ren-hua` 文件夹放进该工具的 Skills 目录即可。

## 怎么用？

在支持技能调用的对话框里输入 `/` 选择「说人话」，或者直接在提示词里喊它：

```text
用说人话技能，把下面这段话彻底改好懂一点，去掉里面的公文腔和 AI 味，但核心数据和限制条件别丢。
```

```text
用说人话技能，给完全不懂技术的业务同事解释一下什么是“接口幂等性”。
```

```text
用说人话技能，把这些零散要点整理成一条发给合作部门的飞书消息，说清目前卡在哪、需要他们周四前配合什么。
```

## 仓库结构

```text
ShuoRenHua/
├── README.md
├── LICENSE
├── CHANGELOG.md
├── assets/
└── shuo-ren-hua/
    ├── SKILL.md                 # 核心规则入口（自带 6 把去 AI 味手术刀与破壳重说原则）
    ├── LICENSE
    ├── agents/
    ├── references/
    │   ├── plain-language.md    # 怎么把难懂的话、长定语、黑话翻译成人话
    │   ├── editing.md           # 怎么既敢“破壳重说”，又守住原意底线
    │   ├── formats.md           # 解释、工作消息、分析、教程怎么看人下菜碟
    │   ├── forum-prose.md       # 公众号、知乎长文、经验帖怎么写出“活人感”
    │   ├── reality.md           # 事实底线、数据口径与录音会议纪要整理
    │   ├── fiction.md           # 故事、小说与人物对白怎么写活
    │   ├── revision.md          # 交稿前的“三遍顺稿法”
    │   ├── rules.json           # 本地检查脚本配置
    │   └── examples/            # 5 类场景的「AI 腔 vs 说人话」完整段落对照库
    └── scripts/                 # 可选的本地辅助检查脚本（不联网、不改稿）
```

## 可选的本地检查工具

日常写稿和改稿不需要跑脚本。如果你在本地审校重要长文，想快速筛一遍超长句、跨结构代词或典型套话词，可以在 `shuo-ren-hua` 目录下运行：

```bash
python3 scripts/check_prose.py article.md --profile general
```

需要核对指定逐字锁定片段时，可配合 `--original` 和 `--contract` 使用（详见 [editing.md](shuo-ren-hua/references/editing.md#附录可选的机器保真契约仅供长文严格审校使用)）。脚本只提供启发式定位提醒，文章好不好懂、像不像人话，永远以实际阅读感受为准。

## 致谢与许可

本项目最初基于 [KKKKhazix/human-writing](https://github.com/KKKKhazix/human-writing) 衍生改进，部分检查器启发式规则与写作方法曾参考 [lieflat-less-ai-tone](https://github.com/larashero3-dotcom/lieflat-less-ai-tone)、Google developer documentation style guide、ASD-STE100 与 [cida](https://github.com/mizzlelover/cida)，在此一并致谢。

技能规则、文档和脚本采用 [MIT 许可证](LICENSE)。
