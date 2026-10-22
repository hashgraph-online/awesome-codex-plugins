// Controller capabilities stay in host memory, never in rendered diagnostics.
// Keep editable IR and execution payloads untouched.
export function displayDetails(value) {
  return JSON.stringify(value, (key, item) =>
    ['control_token', 'lease_token'].includes(key) && item != null ? '[hidden capability]' : item, 2);
}
