class BasicQueue<T> {
  private items: T[] = [];

  enqueue(item: T): void {
    this.items.push(item);
  }

  dequeue(): T | undefined {
    if (this.items.length === 0) {
      return undefined;
    }
    return this.items.shift();
  }

  front(): T | undefined {
    if (this.items.length === 0) {
      return undefined;
    }
    return this.items[0];
  }

  isEmpty(): boolean {
    return this.items.length === 0;
  }

  size(): number {
    return this.items.length;
  }

  toArray(): T[] {
    return this.items.slice();
  }

  clear(): void {
    this.items = [];
  }
}
