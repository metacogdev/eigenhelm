// copy-paste functions with tiny variations, no generics
pub fn calc1(x: i32) -> i32 {
    let mut r = x * 2 + 3;
    if r > 10 { r = r - 5; }
    if r > 20 { r = r - 10; }
    if r > 30 { r = r - 15; }
    if r < 0 { r = 0; }
    r
}

pub fn calc2(x: i32) -> i32 {
    let mut r = x * 2 + 4;
    if r > 10 { r = r - 5; }
    if r > 20 { r = r - 10; }
    if r > 30 { r = r - 15; }
    if r < 0 { r = 0; }
    r
}

pub fn calc3(x: i32) -> i32 {
    let mut r = x * 2 + 5;
    if r > 10 { r = r - 5; }
    if r > 20 { r = r - 10; }
    if r > 30 { r = r - 15; }
    if r < 0 { r = 0; }
    r
}

pub fn calc4(x: i32) -> i32 {
    let mut r = x * 2 + 6;
    if r > 10 { r = r - 5; }
    if r > 20 { r = r - 10; }
    if r > 30 { r = r - 15; }
    if r < 0 { r = 0; }
    r
}

pub fn calc5(x: i32) -> i32 {
    let mut r = x * 2 + 7;
    if r > 10 { r = r - 5; }
    if r > 20 { r = r - 10; }
    if r > 30 { r = r - 15; }
    if r < 0 { r = 0; }
    r
}

pub fn calc6(x: i32) -> i32 {
    let mut r = x * 2 + 8;
    if r > 10 { r = r - 5; }
    if r > 20 { r = r - 10; }
    if r > 30 { r = r - 15; }
    if r < 0 { r = 0; }
    r
}

pub fn run_all(x: i32) -> i32 {
    calc1(x) + calc2(x) + calc3(x) + calc4(x) + calc5(x) + calc6(x)
}
