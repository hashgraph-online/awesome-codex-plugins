export function validateRunReport(report: unknown, plan: unknown, artifactRoot: string): {
  status: 'PASS' | 'FAIL';
  scope: 'report-validation';
  issues: string[];
};
