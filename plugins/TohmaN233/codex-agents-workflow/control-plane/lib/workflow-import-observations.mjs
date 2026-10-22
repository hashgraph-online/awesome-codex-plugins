// Presence of portable resources is not a broken conversion. These legacy
// observations are retained as information; missing/redacted resources still block.
export const informationalImportObservation = issue => [
  'SCRIPT_REQUIRES_REVIEW', 'BINARY_RESOURCE_REQUIRES_CAPABILITY',
  'EXTERNAL_REFERENCE_REQUIRES_REVIEW', 'RUNTIME_PATH_REFERENCE',
  'CONVERSION_AGENT_ASSISTED',
].includes(issue.code);
