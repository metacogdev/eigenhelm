fn fizzbuzz(n: u32) -> String {
    if n % 15 == 0 {
        String::from("FizzBuzz")
    } else if n % 3 == 0 {
        String::from("Fizz")
    } else if n % 5 == 0 {
        String::from("Buzz")
    } else {
        n.to_string()
    }
}

fn run_fizzbuzz(limit: u32) {
    for i in 1..=limit {
        println!("{}", fizzbuzz(i));
    }
}

fn main() {
    run_fizzbuzz(20);
}
