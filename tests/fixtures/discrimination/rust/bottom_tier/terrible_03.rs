// unwrap on everything, no error handling, all owned types
use std::collections::HashMap;

pub fn parse_config(s: String) -> HashMap<String, String> {
    let mut m: HashMap<String, String> = HashMap::new();
    let lines: Vec<String> = s.clone().split("\n").map(|l| l.to_string()).collect();
    for line in lines.clone() {
        let l = line.clone();
        if l.clone().contains("=") {
            let parts: Vec<String> = l.clone().splitn(2, "=").map(|p| p.to_string()).collect();
            let key = parts[0].clone().trim().to_string();
            let val = parts[1].clone().trim().to_string();
            m.insert(key.clone(), val.clone());
        }
    }
    m.clone()
}

pub fn to_config_string(m: HashMap<String, String>) -> String {
    let mut r = String::new();
    let mc = m.clone();
    for (k, v) in mc.clone() {
        let kc = k.clone();
        let vc = v.clone();
        r = r.clone() + &kc.clone() + "=" + &vc.clone() + "\n";
    }
    r.clone()
}

pub fn merge_configs(a: HashMap<String, String>, b: HashMap<String, String>) -> HashMap<String, String> {
    let mut r: HashMap<String, String> = HashMap::new();
    let ac = a.clone();
    for (k, v) in ac.clone() {
        r.insert(k.clone(), v.clone());
    }
    let bc = b.clone();
    for (k, v) in bc.clone() {
        r.insert(k.clone(), v.clone());
    }
    r.clone()
}

pub fn get_or_default(m: HashMap<String, String>, key: String, default_val: String) -> String {
    let mc = m.clone();
    let kc = key.clone();
    match mc.get(&kc) {
        Some(v) => v.clone(),
        None => default_val.clone(),
    }
}
