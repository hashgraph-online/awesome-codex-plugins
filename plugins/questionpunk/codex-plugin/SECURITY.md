# Security policy

## Reporting a vulnerability

Email security reports to jake@questionpunk.com with "Security" in the subject. Include the affected component (this plugin, the hosted MCP endpoint at https://app.questionpunk.com/api/v1, or the QuestionPunk app), steps to reproduce, and the impact you observed. Please do not open a public issue for a vulnerability.

We aim to acknowledge reports within three business days and to share a fix timeline after triage.

## Scope

This repository contains only plugin metadata, skills and a remote MCP connection definition. It ships no credentials, hooks or local server processes. Each user signs in to their own QuestionPunk account through OAuth; never paste an access token or password into a chat.

## Supported versions

Only the latest release on the default branch is supported.
