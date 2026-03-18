class SimpleCache {
  private store: { [key: string]: string } = {};

  set(key: string, value: string): void {
    this.store[key] = value;
  }

  get(key: string): string | undefined {
    if (key in this.store) {
      return this.store[key];
    }
    return undefined;
  }

  has(key: string): boolean {
    return key in this.store;
  }

  delete(key: string): boolean {
    if (key in this.store) {
      delete this.store[key];
      return true;
    }
    return false;
  }

  clear(): void {
    this.store = {};
  }

  size(): number {
    return Object.keys(this.store).length;
  }

  keys(): string[] {
    return Object.keys(this.store);
  }
}
