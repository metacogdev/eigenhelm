class Counter {
  private counts: { [key: string]: number } = {};

  increment(key: string): number {
    if (!(key in this.counts)) {
      this.counts[key] = 0;
    }
    this.counts[key]++;
    return this.counts[key];
  }

  decrement(key: string): number {
    if (!(key in this.counts)) {
      this.counts[key] = 0;
    }
    this.counts[key]--;
    return this.counts[key];
  }

  get(key: string): number {
    if (key in this.counts) {
      return this.counts[key];
    }
    return 0;
  }

  reset(key: string): void {
    this.counts[key] = 0;
  }

  getAll(): { [key: string]: number } {
    const copy: { [key: string]: number } = {};
    for (const key in this.counts) {
      copy[key] = this.counts[key];
    }
    return copy;
  }

  total(): number {
    let sum = 0;
    for (const key in this.counts) {
      sum += this.counts[key];
    }
    return sum;
  }
}
