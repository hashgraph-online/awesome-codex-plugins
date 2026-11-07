# Python SDK Signatures (generated — do not edit)

> Regenerate: `python api/scripts/skill-truth/generate.py`. CI enforces freshness.

### agents

Agent execution operations.

**`agents.enqueue(agent_name: str, input: dict[str, Any] | None = None, output_schema: dict[str, Any] | None = None, run_as: str | None = None) -> AgentRunHandle`**
  Queue an agent and return as soon as the run is accepted.

**`agents.get_run(run_id: str) -> AgentRun`**
  Get the current status and result for an agent run.

**`agents.run(agent_name: str, input: dict[str, Any] | None = None, output_schema: dict[str, Any] | None = None, timeout: float | None = None, run_as: str | None = None) -> dict[str, Any] | str | AgentRunPending`**
  Run an agent and wait for the result.

**`agents.wait(run_id: str, output_schema: dict[str, Any] | None = None, timeout: float | None = None) -> dict[str, Any] | str | AgentRunPending`**
  Wait for a previously enqueued run using short status requests.

### ai



**`ai.complete(prompt: str | None = None, messages: list[dict[str, str]] | None = None, system: str | None = None, response_format: type[T] | None = None, knowledge: list[str] | None = None, max_tokens: int | None = None, org_id: str | None = None, profile: str | None = None, model: str | None = None, timeout: float | None = None, files: list[AIInputFile | ArtifactRef | dict[str, Any]] | None = None) -> AIResponse | T`**

**`ai.create_image(prompt: str, filename: str | None = None) -> ArtifactRef`**
  Generate an image and return one portable artifact reference.

**`ai.create_video(prompt: str, filename: str | None = None, timeout_seconds: float = 1800, poll_interval_seconds: float = 2) -> ArtifactRef`**
  Generate a durable video and return one portable artifact reference.

**`ai.get_model_info() -> dict[str, Any]`**

**`ai.stream(prompt: str | None = None, messages: list[dict[str, str]] | None = None, system: str | None = None, knowledge: list[str] | None = None, max_tokens: int | None = None, org_id: str | None = None, model: str | None = None, files: list[AIInputFile | ArtifactRef | dict[str, Any]] | None = None) -> AsyncGenerator[AIStreamChunk, None]`**

### artifacts

Create, read, and share generated files from workflows.

**`artifacts.create_document(filename: str, format: Literal['pdf', 'docx'], title: str, sections: list[dict[str, Any]], subtitle: str | None = None, page_size: Literal['letter', 'a4'] = 'letter') -> ArtifactRef`**
  Create a flowing PDF or DOCX document and return its reference.

**`artifacts.create_image(filename: str, prompt: str) -> ArtifactRef`**
  Generate an image with the configured image model.

**`artifacts.create_spreadsheet(filename: str, sheets: list[dict[str, Any]]) -> ArtifactRef`**
  Create a styled XLSX workbook and return its reference.

**`artifacts.create_text(filename: str, format: Literal['csv', 'html', 'markdown', 'text', 'json'], content: str) -> ArtifactRef`**
  Create a text-family artifact and return its reference.

**`artifacts.create_video(filename: str, prompt: str, timeout_seconds: float = 1800, poll_interval_seconds: float = 2) -> ArtifactRef`**
  Generate a video through a durable platform job and return its reference.

**`artifacts.get_download_url(ref: ArtifactRef | dict[str, Any]) -> str`**
  Create a short-lived download URL for an authorized ArtifactRef.

**`artifacts.list() -> list[ArtifactRef]`**
  List the latest files available in the active run workspace.

**`artifacts.read(ref: ArtifactRef | dict[str, Any]) -> bytes`**
  Read an ArtifactRef received as workflow or MCP tool input.

**`artifacts.write(filename: str, content: bytes, content_type: str) -> ArtifactRef`**
  Store validated workflow-produced bytes behind an opaque reference.

### config



**`config.delete(key: str, scope: str | None = None) -> bool`**

**`config.get(key: str, default: Any = None, scope: str | None = None) -> Any`**

**`config.list(scope: str | None = None) -> ConfigData`**

**`config.set(key: str, value: Any, is_secret: bool = False, scope: str | None = None) -> None`**

### events

Event publishing operations (async).

**`events.emit(topic: str, data: dict, scope: str | None = None, solution: str | None = None) -> dict`**

### executions



**`executions.get(execution_id: str) -> WorkflowExecution`**

**`executions.get_current_logs(execution_id: str | None = None, start: str = '0', count: int = 100) -> 'list[ExecutionLog]'`**

**`executions.list(workflow_name: str | None = None, status: str | None = None, start_date: str | None = None, end_date: str | None = None, limit: int = 50, workflow_id: str | None = None, continuation_token: str | None = None) -> ExecutionList`**

### files



**`files.delete(path: str, location: str = 'workspace', mode: Mode = 'cloud', expected_version: str | None = None, scope: str | None = None) -> None`**

**`files.exists(path: str, location: str = 'workspace', mode: Mode = 'cloud', scope: str | None = None) -> bool`**

**`files.get_signed_url(path: str, method: Literal['PUT', 'GET'] = 'PUT', content_type: str = 'application/octet-stream', location: str = 'uploads', scope: str | None = None, expires_in: int = 600) -> dict`**

**`files.list(directory: str = '', location: str = 'workspace', mode: Mode = 'cloud', scope: str | None = None) -> list[str]`**

**`files.move(source: str, destination: str, location: str, on_conflict: Literal['error', 'rename'] = 'error', scope: str | None = None, timeout_seconds: float = 14400, poll_interval_seconds: float = 2) -> str`**

**`files.move_many(items: list[dict[str, str]], location: str, on_conflict: Literal['error', 'rename'] = 'error', scope: str | None = None, timeout_seconds: float = 14400, poll_interval_seconds: float = 2) -> list[dict]`**

**`files.read(path: str, location: str = 'workspace', mode: Mode = 'cloud', scope: str | None = None, solution: str | None = None) -> str`**

**`files.read_bytes(path: str, location: str = 'workspace', mode: Mode = 'cloud', scope: str | None = None) -> bytes`**

**`files.search(query: str, is_regex: bool = False, case_sensitive: bool = False, include_pattern: str | None = None, source: str = 'all', solution_id: str | None = None, output_mode: str = 'content', context_lines: int = 1, limit: int = 25, cursor: str | None = None) -> dict`**

**`files.stat(path: str, location: str = 'workspace', mode: Mode = 'cloud', scope: str | None = None) -> dict`**

**`files.write(path: str, content: str, location: str = 'workspace', mode: Mode = 'cloud', expected_version: str | None = None, create_only: bool = False, scope: str | None = None) -> None`**

**`files.write_bytes(path: str, content: bytes, location: str = 'workspace', mode: Mode = 'cloud', expected_version: str | None = None, create_only: bool = False, scope: str | None = None) -> None`**

### forms



**`forms.get(form_id: str) -> FormPublic`**

**`forms.list() -> list[FormPublic]`**

### integrations



**`integrations.delete_mapping(name: str, scope: str) -> bool`**

**`integrations.find_mapping(name: str, entity_id: str) -> IntegrationMappingFindResult | None`**

**`integrations.get(name: str, scope: str | None = None, oauth_scope: str | None = None) -> IntegrationData | None`**

**`integrations.get_mapping(name: str, scope: str | None = None, entity_id: str | None = None) -> IntegrationMappingResponse | None`**

**`integrations.list_mappings(name: str, scope: str | None = None) -> list[IntegrationMappingResponse] | None`**

**`integrations.upsert_mapping(name: str, scope: str, entity_id: str, entity_name: str | None = None, config: dict | None = None) -> IntegrationMappingResponse`**

### knowledge



**`knowledge.delete(key: str, namespace: str = 'default', scope: str | None = None) -> bool`**

**`knowledge.delete_namespace(namespace: str, scope: str | None = None) -> int`**

**`knowledge.get(key: str, namespace: str = 'default', scope: str | None = None) -> KnowledgeDocument | None`**

**`knowledge.list_namespaces(scope: str | None = None, include_global: bool = True) -> list[NamespaceInfo]`**

**`knowledge.search(query: str, namespace: str | list[str] = 'default', limit: int = 5, min_score: float | None = None, metadata_filter: dict[str, Any] | None = None, scope: str | None = None, fallback: bool = True) -> list[KnowledgeDocument]`**

**`knowledge.store(content: str, namespace: str = 'default', key: str | None = None, metadata: dict[str, Any] | None = None, scope: str | None = None) -> str`**

**`knowledge.store_many(documents: list[dict[str, Any]], namespace: str = 'default', scope: str | None = None, timeout: float | None = 300.0) -> list[str]`**

### organizations



**`organizations.create(name: str, domain: str | None = None, is_active: bool = True) -> Organization`**

**`organizations.delete(org_id: str) -> bool`**

**`organizations.get(org_id: str) -> Organization`**

**`organizations.list() -> list[Organization]`**

**`organizations.update(org_id: str, updates: Any) -> Organization`**

### roles



**`roles.assign_forms(role_id: str, form_ids: list[str]) -> None`**

**`roles.assign_users(role_id: str, user_ids: list[str]) -> None`**

**`roles.create(name: str, description: str = '') -> Role`**

**`roles.delete(role_id: str) -> None`**

**`roles.get(role_id: str) -> Role`**

**`roles.list() -> list[Role]`**

**`roles.list_forms(role_id: str) -> list[str]`**

**`roles.list_users(role_id: str) -> list[str]`**

**`roles.update(role_id: str, updates: Any) -> Role`**

### tables



**`tables.bulk_upsert(table: str, documents: list[dict[str, Any]], scope: str | None = None, created_by: str | None = None, updated_by: str | None = None, conflict_retries: int = 2) -> BulkUpsertResult`**

**`tables.count(table: str, where: dict[str, Any] | None = None, scope: str | None = None) -> int`**

**`tables.create(name: str, description: str | None = None, table_schema: dict[str, Any] | None = None, scope: str | None = None, app: str | None = None) -> TableInfo`**

**`tables.delete(table_id: str) -> bool`**

**`tables.delete_batch(table: str, doc_ids: list[str], scope: str | None = None) -> BatchDeleteResult`**

**`tables.delete_document(table: str, doc_id: str, scope: str | None = None) -> bool`**

**`tables.get(table: str, doc_id: str, scope: str | None = None, solution: str | None = None) -> DocumentData | None`**

**`tables.insert(table: str, data: dict[str, Any], id: str | None = None, scope: str | None = None, created_by: str | None = None, solution: str | None = None) -> DocumentData`**

**`tables.insert_batch(table: str, documents: list[dict[str, Any]], scope: str | None = None, created_by: str | None = None) -> BatchResult`**

**`tables.list(scope: str | None = None, app: str | None = None) -> list[TableInfo]`**

**`tables.query(table: str, where: dict[str, Any] | None = None, order_by: str | None = None, order_dir: str = 'asc', limit: int = 100, offset: int = 0, scope: str | None = None, after_document_id: str | None = None, document_id_prefix: str | None = None, skip_count: bool = False, document_ids: list[str] | None = None, solution: str | None = None) -> DocumentList`**

**`tables.update(table: str, doc_id: str, data: dict[str, Any], scope: str | None = None, updated_by: str | None = None) -> DocumentData | None`**

**`tables.upsert(table: str, id: str, data: dict[str, Any], scope: str | None = None, created_by: str | None = None, updated_by: str | None = None) -> DocumentData`**

**`tables.upsert_batch(table: str, documents: list[dict[str, Any]], scope: str | None = None, created_by: str | None = None, updated_by: str | None = None) -> BatchResult`**

### users



**`users.create(email: str, name: str, is_superuser: bool = False, org_id: str | None = None, is_active: bool = True, base_role_id: str | None = None) -> UserPublic`**

**`users.delete(user_id: str) -> bool`**

**`users.get(user_id: str) -> UserPublic | None`**

**`users.list(org_id: str | None = None, include_inactive: bool = False) -> list[UserPublic]`**

**`users.update(user_id: str, updates: Any) -> UserPublic`**

### workflows



**`workflows.cancel(execution_id: str) -> None`**
  Cancel a Scheduled workflow execution.

**`workflows.execute(workflow: str, input_data: dict[str, Any] | None = None, org_id: str | None = None, run_as: str | None = None, solution: str | None = None, scheduled_at: datetime | None = None, delay_seconds: int | None = None) -> str`**

**`workflows.get(execution_id: str) -> WorkflowExecution`**

**`workflows.list() -> list[WorkflowMetadata]`**

