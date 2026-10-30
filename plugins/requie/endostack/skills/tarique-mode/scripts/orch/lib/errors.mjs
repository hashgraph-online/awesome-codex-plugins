// Error classes mapped to exit codes by the CLI:
//   UserError  -> 1, message on stderr prefixed "error:"
//   UsageError -> 1, message plus help text on stderr
//   NotFound   -> 2

export class UserError extends Error {
  constructor(message) {
    super(message);
    this.name = 'UserError';
  }
}

export class UsageError extends UserError {
  constructor(message, helpTopic = null) {
    super(message);
    this.name = 'UsageError';
    this.helpTopic = helpTopic;
  }
}

export class NotFound extends UserError {
  constructor(message) {
    super(message);
    this.name = 'NotFound';
  }
}
