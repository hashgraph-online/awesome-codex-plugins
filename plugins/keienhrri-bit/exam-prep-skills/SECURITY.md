# Security Policy / 安全问题

## Reporting a vulnerability / 报告漏洞

Please report security problems privately through GitHub: open the **Security** tab of this repository and choose **Report a vulnerability**. Do not open a public issue for them.

发现安全问题，请在本仓库的 **Security** 页点 **Report a vulnerability** 私下报告，不要开公开 issue。

## Scope / 范围

This repository contains agent skills (Markdown instructions) and a few local Python scripts. Relevant reports include:

- a script that writes, moves or deletes files outside the workspace it was pointed at;
- a script or instruction that sends workspace content to the network;
- instructions that tell the agent to bypass the user's confirmation for file changes;
- secrets or personal data committed to the repository.

本仓库是 skill（给 AI 的 Markdown 说明）和几个本地 Python 脚本。上面四类问题都欢迎报告：脚本写、移、删到指定工作区以外；脚本或说明把工作区内容发到网络；说明让 AI 跳过用户确认去改文件；仓库里混进了密钥或个人信息。

## Supported versions / 支持的版本

Only the latest release is supported. 只维护最新版本。
