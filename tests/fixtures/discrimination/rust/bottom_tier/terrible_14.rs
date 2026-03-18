// date math reimplemented badly, nested ifs, magic numbers
pub fn days_in_month(m: i32, y: i32) -> i32 {
    if m == 1 { return 31; }
    if m == 2 {
        if y % 4 == 0 {
            if y % 100 == 0 {
                if y % 400 == 0 { return 29; }
                return 28;
            }
            return 29;
        }
        return 28;
    }
    if m == 3 { return 31; }
    if m == 4 { return 30; }
    if m == 5 { return 31; }
    if m == 6 { return 30; }
    if m == 7 { return 31; }
    if m == 8 { return 31; }
    if m == 9 { return 30; }
    if m == 10 { return 31; }
    if m == 11 { return 30; }
    if m == 12 { return 31; }
    -1
}

pub fn days_between(m1: i32, d1: i32, y1: i32, m2: i32, d2: i32, y2: i32) -> i32 {
    let mut total = 0;
    let mut cm = m1;
    let mut cd = d1;
    let mut cy = y1;
    while cy < y2 || (cy == y2 && cm < m2) || (cy == y2 && cm == m2 && cd < d2) {
        cd = cd + 1;
        total = total + 1;
        if cd > days_in_month(cm, cy) {
            cd = 1;
            cm = cm + 1;
            if cm > 12 {
                cm = 1;
                cy = cy + 1;
            }
        }
    }
    total
}

pub fn format_date(m: i32, d: i32, y: i32) -> String {
    let ms = if m < 10 { format!("0{}", m) } else { format!("{}", m) };
    let ds = if d < 10 { format!("0{}", d) } else { format!("{}", d) };
    format!("{}/{}/{}", ms.clone(), ds.clone(), y)
}

pub fn add_days(m: i32, d: i32, y: i32, n: i32) -> String {
    let mut cm = m;
    let mut cd = d;
    let mut cy = y;
    for _i in 0..n {
        cd = cd + 1;
        if cd > days_in_month(cm, cy) {
            cd = 1;
            cm = cm + 1;
            if cm > 12 { cm = 1; cy = cy + 1; }
        }
    }
    format_date(cm, cd, cy)
}
