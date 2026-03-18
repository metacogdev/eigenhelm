class Stack {
  items: number[];

  constructor() {
    this.items = [];
  }

  push(item: number): void {
    this.items.push(item);
  }

  pop(): number | undefined {
    return this.items.pop();
  }

  peek(): number | undefined {
    if (this.items.length === 0) return undefined;
    return this.items[this.items.length - 1];
  }

  size(): number {
    return this.items.length;
  }

  isEmpty(): boolean {
    return this.items.length === 0;
  }
}
