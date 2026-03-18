type StateId = string;
type EventId = string;

interface Transition {
  from: StateId;
  event: EventId;
  to: StateId;
  guard?: () => boolean;
  action?: () => void;
}

interface MachineConfig {
  initial: StateId;
  states: Record<StateId, { onEnter?: () => void; onExit?: () => void }>;
  transitions: Transition[];
}

class StateMachine {
  private current: StateId;
  private readonly states: Map<StateId, { onEnter?: () => void; onExit?: () => void }>;
  private readonly transitionTable: Map<string, Transition[]>;

  constructor(config: MachineConfig) {
    this.current = config.initial;
    this.states = new Map(Object.entries(config.states));
    this.transitionTable = new Map();
    for (const t of config.transitions) {
      const key = `${t.from}:${t.event}`;
      const existing = this.transitionTable.get(key) ?? [];
      existing.push(t);
      this.transitionTable.set(key, existing);
    }
    this.states.get(this.current)?.onEnter?.();
  }

  get state(): StateId { return this.current; }

  send(event: EventId): boolean {
    const candidates = this.transitionTable.get(`${this.current}:${event}`);
    if (!candidates || candidates.length === 0) return false;

    const transition = candidates.find((t) => !t.guard || t.guard());
    if (!transition) return false;

    this.states.get(this.current)?.onExit?.();
    transition.action?.();
    this.current = transition.to;
    this.states.get(this.current)?.onEnter?.();
    return true;
  }

  can(event: EventId): boolean {
    const candidates = this.transitionTable.get(`${this.current}:${event}`);
    if (!candidates) return false;
    return candidates.some((t) => !t.guard || t.guard());
  }

  availableEvents(): EventId[] {
    const events: EventId[] = [];
    for (const [key] of this.transitionTable) {
      const [from, event] = key.split(":");
      if (from === this.current) events.push(event);
    }
    return events;
  }
}
