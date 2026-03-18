fn sum_vec(nums: &[i32]) -> i32 {
    let mut total = 0;
    for n in nums {
        total += n;
    }
    total
}

fn max_vec(nums: &[i32]) -> Option<i32> {
    if nums.is_empty() {
        return None;
    }
    let mut max = nums[0];
    for &n in &nums[1..] {
        if n > max {
            max = n;
        }
    }
    Some(max)
}

fn min_vec(nums: &[i32]) -> Option<i32> {
    if nums.is_empty() {
        return None;
    }
    let mut min = nums[0];
    for &n in &nums[1..] {
        if n < min {
            min = n;
        }
    }
    Some(min)
}

fn average_vec(nums: &[i32]) -> f64 {
    if nums.is_empty() {
        return 0.0;
    }
    sum_vec(nums) as f64 / nums.len() as f64
}

fn count_greater_than(nums: &[i32], threshold: i32) -> usize {
    let mut count = 0;
    for &n in nums {
        if n > threshold {
            count += 1;
        }
    }
    count
}
