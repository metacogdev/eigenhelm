/**
 * Minimal event emitter supporting on, off, once, and emit.
 */
class EventEmitter {
    constructor() {
        this._listeners = new Map();
    }

    on(event, handler) {
        if (!this._listeners.has(event)) {
            this._listeners.set(event, []);
        }
        this._listeners.get(event).push(handler);
        return this;
    }

    off(event, handler) {
        const handlers = this._listeners.get(event);
        if (!handlers) return this;
        const index = handlers.indexOf(handler);
        if (index !== -1) {
            handlers.splice(index, 1);
        }
        return this;
    }

    once(event, handler) {
        const wrapper = (...args) => {
            this.off(event, wrapper);
            handler.apply(this, args);
        };
        wrapper._original = handler;
        return this.on(event, wrapper);
    }

    emit(event, ...args) {
        const handlers = this._listeners.get(event);
        if (!handlers) return false;
        for (const handler of [...handlers]) {
            handler.apply(this, args);
        }
        return true;
    }

    listenerCount(event) {
        const handlers = this._listeners.get(event);
        return handlers ? handlers.length : 0;
    }
}

module.exports = EventEmitter;
