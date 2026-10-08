export class ConnectorError extends Error {
  constructor(code, message, options = {}) {
    super(message);
    this.name = 'ConnectorError';
    this.code = code;
    this.retryable = options.retryable === true;
    this.actionRequired = options.actionRequired || null;
    this.details = options.details || null;
  }
}

export function connectorError(code, message, options = {}) {
  return new ConnectorError(code, message, options);
}

export function publicConnectorError(error) {
  return {
    code: typeof error?.code === 'string' ? error.code : 'CONNECTOR_ERROR',
    message: error instanceof Error ? error.message : String(error),
    retryable: error?.retryable === true,
    action_required: error?.actionRequired || null,
    details: error?.details && typeof error.details === 'object' ? error.details : null,
  };
}
