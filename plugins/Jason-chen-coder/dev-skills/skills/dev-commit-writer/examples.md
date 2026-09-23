# Dev Commit Writer Examples

示例 message 以给定 diff 为依据,不代表已评审或已提交。

## 只要 message

用户:「给个 commit message。」

暂存内容仅为金额格式化函数,历史使用英文 Conventional Commits:

```text
feat: add USD currency formatting
```

无需要求用户额外声明跳过 review。

## 暂存与未暂存不同主题

index 为登录错误提示修复,未暂存包含报表新功能。未指定范围时,说明“以下基于 staged 修改”,输出:

```text
fix(auth): show the server message when login fails
```

不要把报表功能写进这条 message,也不要调整暂存区。

## 用户明确要求覆盖全部改动

diff 含互不依赖的登录修复和报表功能。可以直接给出两个建议 message,并说明对应文件范围,不必等待用户选措辞。若用户明确要求一条合并 message,据实概括两项变化。

## artifact 不相关

目录中只有 `designs/report-export.md`,本次改的是登录错误提示。省略 Refs;无需为了一个不相关 footer 阻塞 message 生成。只有读取内容并确认关系时才引用。

## 仓库使用中文

历史风格为简短中文动词开头,当前 diff 新增导出取消处理:

```text
支持取消进行中的报表导出
```

简单意图不需要正文,没有证据的验证结果也不能加入 message。
