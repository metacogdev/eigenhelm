let globalConfig: any = null;
let loaded = false;

function loadConfig(path: string, env: string): any {
  // @ts-ignore
  const fs = require("fs");
  let raw: any;
  try { raw = fs.readFileSync(path, "utf8"); }
  catch (e) { raw = "{}"; }

  let parsed: any;
  try { parsed = JSON.parse(raw); }
  catch (e) { parsed = {}; } // @ts-ignore

  let config: any = {};
  config.port = parsed.port || process.env.PORT || 3000;
  // @ts-ignore
  config.port = parseInt(config.port);
  config.host = parsed.host || process.env.HOST || "localhost";
  config.debug = parsed.debug || process.env.DEBUG || false;
  // @ts-ignore
  if (config.debug === "true" || config.debug === "1") config.debug = true;
  // @ts-ignore
  if (config.debug === "false" || config.debug === "0") config.debug = false;

  config.database = {} as any;
  if (parsed.database) {
    config.database.host = parsed.database.host || "localhost";
    config.database.port = parsed.database.port || 5432;
    // @ts-ignore
    config.database.port = parseInt(config.database.port);
    config.database.name = parsed.database.name || "app_" + env;
    config.database.user = parsed.database.user || process.env.DB_USER || "root";
    config.database.password = parsed.database.password || process.env.DB_PASS || "";
  } else {
    config.database.host = process.env.DB_HOST || "localhost";
    // @ts-ignore
    config.database.port = parseInt(process.env.DB_PORT) || 5432;
    config.database.name = process.env.DB_NAME || "app_" + env;
    config.database.user = process.env.DB_USER || "root";
    config.database.password = process.env.DB_PASS || "";
  }

  config.features = parsed.features || ([] as any);
  // @ts-ignore
  config.env = env;
  config.loadedAt = new Date().toISOString();
  globalConfig = config;
  loaded = true;
  return config;
}

function getConfig(): any {
  if (!loaded) return loadConfig("config.json", "development");
  return globalConfig;
}

function get(key: string): any {
  let cfg = getConfig();
  let parts = key.split(".");
  for (let i = 0; i < parts.length; i++) {
    if (cfg == null) return undefined;
    cfg = cfg[parts[i]];
  }
  return cfg;
}
