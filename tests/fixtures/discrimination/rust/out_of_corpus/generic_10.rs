fn validate_password(password: &str) -> Result<(), String> {
    if password.len() < 8 {
        return Err(String::from("too short"));
    }
    let mut has_upper = false;
    let mut has_lower = false;
    let mut has_digit = false;
    for ch in password.chars() {
        if ch.is_uppercase() {
            has_upper = true;
        }
        if ch.is_lowercase() {
            has_lower = true;
        }
        if ch.is_ascii_digit() {
            has_digit = true;
        }
    }
    if !has_upper {
        return Err(String::from("needs uppercase"));
    }
    if !has_lower {
        return Err(String::from("needs lowercase"));
    }
    if !has_digit {
        return Err(String::from("needs digit"));
    }
    Ok(())
}

fn validate_email(email: &str) -> bool {
    if !email.contains('@') {
        return false;
    }
    let parts: Vec<&str> = email.split('@').collect();
    if parts.len() != 2 {
        return false;
    }
    if parts[0].is_empty() || parts[1].is_empty() {
        return false;
    }
    parts[1].contains('.')
}
