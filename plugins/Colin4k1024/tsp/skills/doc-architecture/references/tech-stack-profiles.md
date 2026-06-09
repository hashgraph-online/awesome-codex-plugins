# Tech Stack Profiles

用于在文档中锁定示例风格与术语，不替代真实代码标准。

## java-spring-boot

- 契约表达：REST + OpenAPI
- 文档术语：Controller / Service / Repository / DTO
- 重点：事务边界、鉴权、数据库索引

## typescript-next

- 契约表达：HTTP API + typed client
- 文档术语：Route / Server Component / Client State
- 重点：状态分层、响应式、A11y 与性能

## python-fastapi

- 契约表达：FastAPI schema + pydantic
- 文档术语：Router / Service / Dependency
- 重点：输入边界、异常处理、可观测性

## go-service

- 契约表达：REST/gRPC
- 文档术语：Handler / Service / Repository
- 重点：并发语义、超时、资源回收

## composite-profile

- 同时存在后端与前端时，文档需包含页面-域映射，并在 `test-plan.md` 覆盖前后端关键路径。
