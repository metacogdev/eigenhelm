// manual CSV parser, all String, clone everywhere, no traits
pub fn parse_csv(s: String) -> Vec<Vec<String>> {
    let mut rows: Vec<Vec<String>> = Vec::new();
    let mut current_row: Vec<String> = Vec::new();
    let mut current_cell = String::new();
    let mut in_quote = false;
    let chars: Vec<char> = s.clone().chars().collect();
    let mut i = 0;
    while i < chars.clone().len() {
        let c = chars[i];
        if c == '"' {
            if in_quote {
                if i + 1 < chars.clone().len() && chars[i + 1] == '"' {
                    current_cell = current_cell.clone() + "\"";
                    i = i + 1;
                } else {
                    in_quote = false;
                }
            } else {
                in_quote = true;
            }
        } else if c == ',' && !in_quote {
            current_row.push(current_cell.clone());
            current_cell = String::new();
        } else if c == '\n' && !in_quote {
            current_row.push(current_cell.clone());
            current_cell = String::new();
            rows.push(current_row.clone());
            current_row = Vec::new();
        } else {
            current_cell = current_cell.clone() + &String::from(c);
        }
        i = i + 1;
    }
    if current_cell.clone().len() > 0 || current_row.clone().len() > 0 {
        current_row.push(current_cell.clone());
        rows.push(current_row.clone());
    }
    rows.clone()
}

pub fn to_csv(rows: Vec<Vec<String>>) -> String {
    let mut s = String::new();
    for i in 0..rows.clone().len() {
        let row = rows[i].clone();
        for j in 0..row.clone().len() {
            if j > 0 { s = s.clone() + ","; }
            let cell = row[j].clone();
            let mut need_quote = false;
            for c in cell.clone().chars() {
                if c == ',' || c == '"' || c == '\n' { need_quote = true; }
            }
            if need_quote {
                s = s.clone() + "\"";
                for c in cell.clone().chars() {
                    if c == '"' { s = s.clone() + "\"\""; }
                    else { s = s.clone() + &String::from(c); }
                }
                s = s.clone() + "\"";
            } else {
                s = s.clone() + &cell.clone();
            }
        }
        s = s.clone() + "\n";
    }
    s.clone()
}
