interface RegistryEntry {
  key: string;
  value: string;
}

class BasicRegistry {
  private entries: RegistryEntry[] = [];

  register(key: string, value: string): void {
    for (let i = 0; i < this.entries.length; i++) {
      if (this.entries[i].key === key) {
        this.entries[i].value = value;
        return;
      }
    }
    this.entries.push({ key, value });
  }

  get(key: string): string | undefined {
    for (const entry of this.entries) {
      if (entry.key === key) {
        return entry.value;
      }
    }
    return undefined;
  }

  remove(key: string): boolean {
    for (let i = 0; i < this.entries.length; i++) {
      if (this.entries[i].key === key) {
        this.entries.splice(i, 1);
        return true;
      }
    }
    return false;
  }

  has(key: string): boolean {
    return this.get(key) !== undefined;
  }

  keys(): string[] {
    const result: string[] = [];
    for (const entry of this.entries) {
      result.push(entry.key);
    }
    return result;
  }

  size(): number {
    return this.entries.length;
  }
}
