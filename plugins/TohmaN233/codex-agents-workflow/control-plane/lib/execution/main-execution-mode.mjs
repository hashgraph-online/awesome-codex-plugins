export const isOrchestrationMain = node => node?.executor?.kind === 'main' && node.executor.mode === 'orchestration';
export const isWorkerMain = node => node?.executor?.kind === 'main' && !isOrchestrationMain(node);
export const hasOrchestrationMain = workflow => workflow.nodes.some(isOrchestrationMain);
