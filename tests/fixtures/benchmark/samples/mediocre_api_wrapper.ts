interface RequestConfig {
  baseUrl: string;
  timeout?: number;
  headers?: any;
}

class ApiWrapper {
  private config: RequestConfig;
  private cache: any = {};

  constructor(config: RequestConfig) {
    this.config = config;
    if (!this.config.headers) {
      this.config.headers = {};
    }
  }

  setHeader(key: string, value: string): void {
    this.config.headers[key] = value;
  }

  async get(path: string, params?: any): Promise<any> {
    const cacheKey = path + JSON.stringify(params || {});
    if (this.cache[cacheKey]) {
      return this.cache[cacheKey];
    }

    let url = this.config.baseUrl + path;
    if (params) {
      const qs = Object.keys(params)
        .map((k) => `${k}=${encodeURIComponent(params[k])}`)
        .join("&");
      url += "?" + qs;
    }

    const resp = await fetch(url, {
      headers: this.config.headers,
      signal: AbortSignal.timeout(this.config.timeout || 30000),
    });

    const data = await resp.json() as any;
    this.cache[cacheKey] = data;
    return data;
  }

  async post(path: string, body: any): Promise<any> {
    const resp = await fetch(this.config.baseUrl + path, {
      method: "POST",
      headers: { ...this.config.headers, "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(this.config.timeout || 30000),
    });
    return await resp.json() as any;
  }

  async put(path: string, body: any): Promise<any> {
    const resp = await fetch(this.config.baseUrl + path, {
      method: "PUT",
      headers: { ...this.config.headers, "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(this.config.timeout || 30000),
    });
    return await resp.json() as any;
  }

  async delete(path: string): Promise<any> {
    const resp = await fetch(this.config.baseUrl + path, {
      method: "DELETE",
      headers: this.config.headers,
      signal: AbortSignal.timeout(this.config.timeout || 30000),
    });
    return await resp.json() as any;
  }

  clearCache(): void {
    this.cache = {};
  }
}
