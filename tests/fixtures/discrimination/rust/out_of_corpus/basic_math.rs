fn add(a: i32, b: i32) -> i32 {
    a + b
}

fn subtract(a: i32, b: i32) -> i32 {
    a - b
}

fn multiply(a: i32, b: i32) -> i32 {
    a * b
}

fn divide(a: i32, b: i32) -> i32 {
    if b == 0 {
        println!("Cannot divide by zero");
        return 0;
    }
    a / b
}

fn main() {
    println!("{}", add(2, 3));
    println!("{}", subtract(10, 4));
    println!("{}", multiply(3, 7));
    println!("{}", divide(10, 2));
}
