// Preserve reported work first; list order only breaks ties within the same state.
export function selectProgressTarget<T extends { readonly status: string }>(
  items: readonly T[],
): T | undefined {
  return (
    items.find((item) => item.status === "active") ??
    items.find((item) => item.status === "pending") ??
    items.find((item) => item.status === "blocked")
  );
}
