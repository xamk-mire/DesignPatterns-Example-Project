export type RealtimeEvent = { type: string; payload: unknown };

// Phase 12 replaces this no-op with a WebSocket subscription.
export function subscribeRealtime(_handler: (event: RealtimeEvent) => void): () => void {
  return () => undefined;
}
