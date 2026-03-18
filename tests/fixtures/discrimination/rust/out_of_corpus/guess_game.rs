fn check_guess(guess: i32, answer: i32) -> &'static str {
    if guess < answer {
        "Too low"
    } else if guess > answer {
        "Too high"
    } else {
        "Correct!"
    }
}

fn count_tries(guesses: &[i32], answer: i32) -> usize {
    let mut count = 0;
    for g in guesses {
        count += 1;
        if *g == answer {
            break;
        }
    }
    count
}

fn main() {
    let answer = 42;
    let guesses = vec![10, 30, 50, 42];
    for g in &guesses {
        println!("{}: {}", g, check_guess(*g, answer));
    }
    println!("Took {} tries", count_tries(&guesses, answer));
}
