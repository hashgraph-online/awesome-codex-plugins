/** Use only the exact already-read or committed state at a Host boundary. */
export function committedTerminalOutput(state){
  return state.status==='succeeded'&&Object.hasOwn(state,'output')
    ?{output:structuredClone(state.output)}:{};
}

/** Public completion facts come from the same committed state, without another read. */
export function committedTerminalCompletion(state){
  if(!['succeeded','failed','cancelled'].includes(state.status))return {};
  return {completion_satisfied:state.status==='succeeded',recovery_required:state.status==='failed',
    ...committedTerminalOutput(state)};
}
