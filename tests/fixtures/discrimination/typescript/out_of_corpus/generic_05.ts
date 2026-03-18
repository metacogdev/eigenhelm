class StateHolder<T> {
  private state: T;
  private history: T[] = [];

  constructor(initial: T) {
    this.state = initial;
  }

  get(): T {
    return this.state;
  }

  set(value: T): void {
    this.history.push(this.state);
    this.state = value;
  }

  undo(): boolean {
    if (this.history.length === 0) {
      return false;
    }
    this.state = this.history.pop()!;
    return true;
  }

  getHistory(): T[] {
    return this.history.slice();
  }

  getHistoryLength(): number {
    return this.history.length;
  }
}
