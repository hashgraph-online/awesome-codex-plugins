function extractPatchedFiles(patch) {
  if (!patch) return [];

  const files = [];
  for (const line of patch.split('\n')) {
    if (line.startsWith('*** Update File: ')) {
      files.push(line.slice('*** Update File: '.length).trim());
      continue;
    }
    if (line.startsWith('*** Add File: ')) {
      files.push(line.slice('*** Add File: '.length).trim());
      continue;
    }
    if (line.startsWith('*** Delete File: ')) {
      files.push(line.slice('*** Delete File: '.length).trim());
    }
  }

  return Array.from(new Set(files.filter(Boolean)));
}

function normalizeHookInput(rawInput) {
  let input;
  try {
    input = JSON.parse(rawInput);
  } catch (err) {
    process.stderr.write('[boss-skill] normalizeHookInput: ' + err.message + '\n');
    return null;
  }

  // Claude-style hooks use tool_input/tool_name; Codex apply_patch and Bash payloads observed in tests use arguments/tool.
  const toolInput = input.tool_input || input.arguments || {};
  const directFilePath = toolInput.file_path || toolInput.path || '';
  const command = toolInput.command || '';
  const patch =
    toolInput.patch ||
    (input.tool_name === 'apply_patch' || input.tool === 'apply_patch' ? command : '');
  const filePaths = directFilePath ? [directFilePath] : extractPatchedFiles(patch);

  return {
    rawInput: input,
    eventName: input.hook_event_name || '',
    cwd: input.cwd || '',
    toolName: input.tool_name || input.tool || '',
    toolInput,
    filePaths,
    patch,
    command,
    permissionMode: input.permission_mode || '',
    turnId: input.turn_id || '',
    stopHookActive: input.stop_hook_active,
  };
}

export { extractPatchedFiles, normalizeHookInput };
