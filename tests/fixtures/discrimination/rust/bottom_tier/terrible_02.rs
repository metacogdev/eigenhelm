// massive match with duplicated arms, no traits
pub fn classify(x: i32) -> String {
    match x {
        0 => String::from("zero"),
        1 => String::from("one"),
        2 => String::from("two"),
        3 => String::from("three"),
        4 => String::from("four"),
        5 => String::from("five"),
        6 => String::from("six"),
        7 => String::from("seven"),
        8 => String::from("eight"),
        9 => String::from("nine"),
        10 => String::from("ten"),
        11 => String::from("eleven"),
        12 => String::from("twelve"),
        13 => String::from("thirteen"),
        14 => String::from("fourteen"),
        15 => String::from("fifteen"),
        16 => String::from("sixteen"),
        17 => String::from("seventeen"),
        18 => String::from("eighteen"),
        19 => String::from("nineteen"),
        20 => String::from("twenty"),
        _ => String::from("other"),
    }
}

pub fn classify_range(x: i32) -> String {
    if x > 0 {
        if x > 10 {
            if x > 100 {
                if x > 1000 {
                    String::from("huge")
                } else {
                    String::from("big")
                }
            } else {
                String::from("medium")
            }
        } else {
            String::from("small")
        }
    } else if x < 0 {
        if x < -10 {
            if x < -100 {
                if x < -1000 {
                    String::from("neg-huge")
                } else {
                    String::from("neg-big")
                }
            } else {
                String::from("neg-medium")
            }
        } else {
            String::from("neg-small")
        }
    } else {
        String::from("zero")
    }
}

pub fn batch_classify(items: Vec<i32>) -> Vec<String> {
    let mut r: Vec<String> = Vec::new();
    for item in items.clone() {
        r.push(classify(item.clone()));
    }
    r.clone()
}
