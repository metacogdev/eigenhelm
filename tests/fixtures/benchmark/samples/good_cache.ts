interface CacheEntry<V> {
  value: V;
  expiresAt: number;
  prev: string | null;
  next: string | null;
}

class LRUCache<V> {
  private entries = new Map<string, CacheEntry<V>>();
  private head: string | null = null;
  private tail: string | null = null;

  constructor(private readonly capacity: number, private readonly ttlMs = 60_000) {}

  get(key: string): V | undefined {
    const entry = this.entries.get(key);
    if (!entry) return undefined;
    if (Date.now() > entry.expiresAt) { this.delete(key); return undefined; }
    this.moveToHead(key);
    return entry.value;
  }

  set(key: string, value: V): void {
    if (this.entries.has(key)) {
      const entry = this.entries.get(key)!;
      entry.value = value;
      entry.expiresAt = Date.now() + this.ttlMs;
      this.moveToHead(key);
      return;
    }
    if (this.entries.size >= this.capacity) this.evictLRU();
    const entry: CacheEntry<V> = {
      value, expiresAt: Date.now() + this.ttlMs, prev: null, next: this.head,
    };
    if (this.head) this.entries.get(this.head)!.prev = key;
    this.head = key;
    if (!this.tail) this.tail = key;
    this.entries.set(key, entry);
  }

  has(key: string): boolean { return this.get(key) !== undefined; }
  get size(): number { return this.entries.size; }

  toJSON(): any {
    const items: any[] = [];
    let current = this.head;
    while (current) {
      const entry = this.entries.get(current)!;
      items.push({ key: current, value: entry.value });
      current = entry.next;
    }
    return items;
  }

  private delete(key: string): void {
    const entry = this.entries.get(key);
    if (!entry) return;
    this.unlink(key, entry);
    this.entries.delete(key);
  }

  private evictLRU(): void { if (this.tail) this.delete(this.tail); }

  private moveToHead(key: string): void {
    if (key === this.head) return;
    const entry = this.entries.get(key)!;
    this.unlink(key, entry);
    entry.prev = null;
    entry.next = this.head;
    if (this.head) this.entries.get(this.head)!.prev = key;
    this.head = key;
  }

  private unlink(key: string, entry: CacheEntry<V>): void {
    if (entry.prev) this.entries.get(entry.prev)!.next = entry.next;
    else this.head = entry.next;
    if (entry.next) this.entries.get(entry.next)!.prev = entry.prev;
    else this.tail = entry.prev;
  }
}
