interface ConfigEntry {
  key: string;
  value: string;
}

function parseConfigLine(line: string): ConfigEntry | null {
  const trimmed = line.trim();
  if (trimmed === "" || trimmed.startsWith("#")) {
    return null;
  }
  const eqIndex = trimmed.indexOf("=");
  if (eqIndex === -1) {
    return null;
  }
  const key = trimmed.substring(0, eqIndex).trim();
  const value = trimmed.substring(eqIndex + 1).trim();
  return { key, value };
}

function parseConfig(text: string): ConfigEntry[] {
  const lines = text.split("\n");
  const entries: ConfigEntry[] = [];
  for (const line of lines) {
    const entry = parseConfigLine(line);
    if (entry !== null) {
      entries.push(entry);
    }
  }
  return entries;
}

function configToObject(entries: ConfigEntry[]): { [key: string]: string } {
  const obj: { [key: string]: string } = {};
  for (const entry of entries) {
    obj[entry.key] = entry.value;
  }
  return obj;
}

function getConfigValue(entries: ConfigEntry[], key: string): string | undefined {
  for (const entry of entries) {
    if (entry.key === key) {
      return entry.value;
    }
  }
  return undefined;
}
