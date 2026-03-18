// string building HTML, all owned, clone everything
pub fn make_table(data: Vec<Vec<String>>) -> String {
    let mut h = String::new();
    h = h.clone() + "<table>";
    h = h.clone() + "<thead><tr>";
    h = h.clone() + "<th style='padding:8px;background:#333;color:#fff'>Col1</th>";
    h = h.clone() + "<th style='padding:8px;background:#333;color:#fff'>Col2</th>";
    h = h.clone() + "<th style='padding:8px;background:#333;color:#fff'>Col3</th>";
    h = h.clone() + "</tr></thead>";
    h = h.clone() + "<tbody>";
    for i in 0..data.clone().len() {
        let row = data[i].clone();
        if i % 2 == 0 {
            h = h.clone() + "<tr style='background:#f9f9f9'>";
        } else {
            h = h.clone() + "<tr style='background:#ffffff'>";
        }
        for j in 0..row.clone().len() {
            let cell = row[j].clone();
            h = h.clone() + "<td style='padding:8px;border:1px solid #ddd'>";
            h = h.clone() + &cell.clone();
            h = h.clone() + "</td>";
        }
        h = h.clone() + "</tr>";
    }
    h = h.clone() + "</tbody></table>";
    h.clone()
}

pub fn make_list(items: Vec<String>) -> String {
    let mut h = String::new();
    h = h.clone() + "<ul>";
    for i in 0..items.clone().len() {
        let item = items[i].clone();
        h = h.clone() + "<li style='padding:4px'>";
        h = h.clone() + &format!("{}. {}", i + 1, item.clone());
        h = h.clone() + "</li>";
    }
    h = h.clone() + "</ul>";
    h.clone()
}
