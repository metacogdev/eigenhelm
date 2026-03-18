use std::collections::HashMap;
use std::num::ParseIntError;

#[derive(Debug)]
pub enum ConfigError {
    MissingKey(String),
    InvalidValue(String, ParseIntError),
    OutOfRange { key: String, value: i64, max: i64 },
}

pub struct Config {
    entries: HashMap<String, String>,
}

impl Config {
    pub fn new(entries: HashMap<String, String>) -> Self {
        Self { entries }
    }

    fn get_raw(&self, key: &str) -> Result<&str, ConfigError> {
        self.entries
            .get(key)
            .map(|s| s.as_str())
            .ok_or_else(|| ConfigError::MissingKey(key.to_owned()))
    }

    fn parse_bounded(&self, key: &str, max: i64) -> Result<i64, ConfigError> {
        self.get_raw(key)
            .and_then(|raw| {
                raw.parse::<i64>()
                    .map_err(|e| ConfigError::InvalidValue(key.to_owned(), e))
            })
            .and_then(|val| {
                if val > max {
                    Err(ConfigError::OutOfRange { key: key.to_owned(), value: val, max })
                } else {
                    Ok(val)
                }
            })
    }

    pub fn load_server_settings(&self) -> Result<(i64, i64, String), ConfigError> {
        let port = self.parse_bounded("port", 65535)?;
        let workers = self.parse_bounded("workers", 256)?;
        let host = self.get_raw("host").map(|s| s.to_owned()).unwrap_or_else(|_| "0.0.0.0".into());
        Ok((port, workers, host))
    }
}
