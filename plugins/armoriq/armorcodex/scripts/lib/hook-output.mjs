export function denyPreTool(reason) {
  return {
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "deny",
      permissionDecisionReason: reason
    }
  };
}

export function denyPermissionRequest(reason) {
  return {
    hookSpecificOutput: {
      hookEventName: "PermissionRequest",
      decision: {
        behavior: "deny",
        message: reason
      }
    }
  };
}

export function blockPrompt(reason) {
  return {
    decision: "block",
    reason
  };
}

export function addPromptContext(context, hookEventName = "UserPromptSubmit") {
  return {
    hookSpecificOutput: {
      hookEventName,
      additionalContext: context
    }
  };
}
