fn celsius_to_fahrenheit(c: f64) -> f64 {
    c * 9.0 / 5.0 + 32.0
}

fn fahrenheit_to_celsius(f: f64) -> f64 {
    (f - 32.0) * 5.0 / 9.0
}

fn print_table() {
    let temps = [0.0, 20.0, 37.0, 100.0];
    for t in temps {
        let f = celsius_to_fahrenheit(t);
        println!("{:.1}C = {:.1}F", t, f);
    }
}

fn main() {
    print_table();
}
