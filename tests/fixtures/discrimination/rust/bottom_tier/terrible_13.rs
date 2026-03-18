// deeply nested validation, unwrap, String everywhere
pub fn validate(data: Vec<(String, String)>) -> (bool, Vec<String>) {
    let mut errors: Vec<String> = Vec::new();
    let mut has_name = false;
    let mut has_age = false;
    let mut has_email = false;
    for pair in data.clone() {
        let k = pair.0.clone();
        let v = pair.1.clone();
        if k.clone() == String::from("name") {
            has_name = true;
            if v.clone().len() > 0 {
                if v.clone().len() <= 255 {
                    // ok
                } else {
                    errors.push(String::from("name too long"));
                }
            } else {
                errors.push(String::from("name empty"));
            }
        } else if k.clone() == String::from("age") {
            has_age = true;
            let parsed = v.clone().parse::<i32>();
            match parsed {
                Ok(a) => {
                    if a >= 0 {
                        if a <= 150 {
                            // ok
                        } else {
                            errors.push(String::from("age too high"));
                        }
                    } else {
                        errors.push(String::from("age negative"));
                    }
                }
                Err(_) => {
                    errors.push(String::from("age not number"));
                }
            }
        } else if k.clone() == String::from("email") {
            has_email = true;
            if v.clone().len() > 0 {
                let mut has_at = false;
                for c in v.clone().chars() {
                    if c == '@' { has_at = true; }
                }
                if !has_at {
                    errors.push(String::from("email no @"));
                }
            } else {
                errors.push(String::from("email empty"));
            }
        }
    }
    if !has_name { errors.push(String::from("name missing")); }
    if !has_age { errors.push(String::from("age missing")); }
    if !has_email { errors.push(String::from("email missing")); }
    (errors.clone().len() == 0, errors.clone())
}
