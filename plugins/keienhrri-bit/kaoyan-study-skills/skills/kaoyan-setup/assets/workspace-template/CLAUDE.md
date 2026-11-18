@AGENTS.md

## Claude Code 专用

- 默认用简体中文；专业术语第一次出现时附英文。
- 讲题时先让我自己做，再指出错在哪一步；讲解给推导过程和依据，不只给结论。
- 这些事交给对应的 skill：讲题 `kaoyan-tutor`、交卷判分 `kaoyan-grading`、阶段复盘和周计划 `kaoyan-plan`、学习记录归档 `kaoyan-archive`、每日资料包 `kaoyan-daily-pack`、PDF 报告和讲义 `kaoyan-report`、纠错复盘 `kaoyan-retro`、物理画图讲几何 `physics-svg-tutor`。
- **照片不进主会话**：答卷照片交给转录者（子代理或另一个模型），主会话只读转录稿。
- **外援的文字不进成稿**：子代理和其他模型只交转录稿、问题清单和独立算出的数字；给我看的成稿由主会话写。例外：约 5000 字以上、不需要新推导的长讲义按 `kaoyan.yaml` 的 `roles.long_writer` 交 `writer` 子代理照主会话的大纲和核过的数字写，主会话核数字、看机检后再给我。一份成稿只审一次。
- 会话很长了、或我离开一个多小时再回来，提醒我开新会话接着做。
