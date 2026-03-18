type EventMap = Record<string, unknown>;
type Handler<T> = (payload: T) => void;

interface TypedEmitter<Events extends EventMap> {
  on<K extends keyof Events>(event: K, handler: Handler<Events[K]>): () => void;
  emit<K extends keyof Events>(event: K, payload: Events[K]): void;
  once<K extends keyof Events>(event: K, handler: Handler<Events[K]>): () => void;
  listenerCount<K extends keyof Events>(event: K): number;
}

function createEmitter<Events extends EventMap>(): TypedEmitter<Events> {
  const listeners = new Map<keyof Events, Set<Handler<unknown>>>();

  function getHandlers<K extends keyof Events>(event: K): Set<Handler<unknown>> {
    let handlers = listeners.get(event);
    if (!handlers) {
      handlers = new Set();
      listeners.set(event, handlers);
    }
    return handlers;
  }

  return {
    on<K extends keyof Events>(event: K, handler: Handler<Events[K]>): () => void {
      const handlers = getHandlers(event);
      handlers.add(handler as Handler<unknown>);
      return () => {
        handlers.delete(handler as Handler<unknown>);
      };
    },

    emit<K extends keyof Events>(event: K, payload: Events[K]): void {
      const handlers = listeners.get(event);
      if (handlers) {
        for (const handler of handlers) {
          handler(payload);
        }
      }
    },

    once<K extends keyof Events>(event: K, handler: Handler<Events[K]>): () => void {
      const wrappedHandler: Handler<Events[K]> = (payload) => {
        unsubscribe();
        handler(payload);
      };
      const unsubscribe = this.on(event, wrappedHandler);
      return unsubscribe;
    },

    listenerCount<K extends keyof Events>(event: K): number {
      return listeners.get(event)?.size ?? 0;
    },
  };
}
