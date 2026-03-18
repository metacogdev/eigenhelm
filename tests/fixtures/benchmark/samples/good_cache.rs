use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};

struct CacheEntry<V> {
    value: V,
    inserted_at: Instant,
}

pub struct TtlCache<V: Clone> {
    store: Arc<Mutex<HashMap<String, CacheEntry<V>>>>,
    ttl: Duration,
}

impl<V: Clone> TtlCache<V> {
    pub fn new(ttl_secs: u64) -> Self {
        let cache = TtlCache {
            store: Arc::new(Mutex::new(HashMap::new())),
            ttl: Duration::from_secs(ttl_secs),
        };
        cache
    }

    pub fn get(&self, key: &str) -> Option<V> {
        let mut store = self.store.lock().expect("lock poisoned");
        if let Some(entry) = store.get(key) {
            if entry.inserted_at.elapsed() < self.ttl {
                let value = entry.value.clone();
                return Some(value);
            } else {
                store.remove(key);
                return None;
            }
        }
        None
    }

    pub fn insert(&self, key: String, value: V) {
        let mut store = self.store.lock().expect("lock poisoned");
        let entry = CacheEntry {
            value: value,
            inserted_at: Instant::now(),
        };
        store.insert(key, entry);
    }

    pub fn remove(&self, key: &str) -> bool {
        let mut store = self.store.lock().expect("lock poisoned");
        store.remove(key).is_some()
    }

    pub fn purge_expired(&self) -> usize {
        let mut store = self.store.lock().expect("lock poisoned");
        let before = store.len();
        store.retain(|_k, entry| entry.inserted_at.elapsed() < self.ttl);
        let after = store.len();
        before - after
    }
}
