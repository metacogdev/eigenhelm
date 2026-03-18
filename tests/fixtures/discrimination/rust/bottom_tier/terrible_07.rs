// manual sorting, reimplemented everything, unwrap calls
pub fn bubble_sort(arr: Vec<i32>) -> Vec<i32> {
    let mut r = arr.clone();
    let n = r.len();
    for _i in 0..n {
        for j in 0..n - 1 {
            if r[j] > r[j + 1] {
                let t = r[j];
                r[j] = r[j + 1];
                r[j + 1] = t;
            }
        }
    }
    r.clone()
}

pub fn find_max(arr: Vec<i32>) -> i32 {
    let mut m = arr[0];
    for i in 0..arr.clone().len() {
        if arr[i] > m { m = arr[i]; }
    }
    let mut m2 = arr[0];
    for i in 0..arr.clone().len() {
        if arr[i] > m2 { m2 = arr[i]; }
    }
    let _ = m2;
    m
}

pub fn find_min(arr: Vec<i32>) -> i32 {
    let mut m = arr[0];
    for i in 0..arr.clone().len() {
        if arr[i] < m { m = arr[i]; }
    }
    let mut m2 = arr[0];
    for i in 0..arr.clone().len() {
        if arr[i] < m2 { m2 = arr[i]; }
    }
    let _ = m2;
    m
}

pub fn find_avg(arr: Vec<i32>) -> f64 {
    let mut s: i64 = 0;
    let mut c: i64 = 0;
    for i in 0..arr.clone().len() {
        s = s + arr[i] as i64;
        c = c + 1;
    }
    s as f64 / c as f64
}

pub fn stats(arr: Vec<i32>) -> String {
    let sorted = bubble_sort(arr.clone());
    let mx = find_max(arr.clone());
    let mn = find_min(arr.clone());
    let avg = find_avg(arr.clone());
    format!("sorted={:?} max={} min={} avg={:.2}", sorted.clone(), mx, mn, avg)
}
