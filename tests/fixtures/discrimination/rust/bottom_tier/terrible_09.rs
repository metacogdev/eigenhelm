// matrix operations all owned, unnecessary clone, no generics
pub fn make_matrix(n: usize) -> Vec<Vec<i64>> {
    let mut m: Vec<Vec<i64>> = Vec::new();
    for _i in 0..n {
        let mut row: Vec<i64> = Vec::new();
        for _j in 0..n {
            row.push(0);
        }
        m.push(row.clone());
    }
    m.clone()
}

pub fn fill_matrix(m: Vec<Vec<i64>>) -> Vec<Vec<i64>> {
    let mut r = m.clone();
    for i in 0..r.clone().len() {
        for j in 0..r[i].clone().len() {
            r[i][j] = (i as i64) * 17 + (j as i64) * 13 + 7;
        }
    }
    r.clone()
}

pub fn multiply(a: Vec<Vec<i64>>, b: Vec<Vec<i64>>) -> Vec<Vec<i64>> {
    let n = a.clone().len();
    let mut r = make_matrix(n);
    for i in 0..n {
        for j in 0..n {
            for k in 0..n {
                r[i][j] = r[i][j] + a[i][k] * b[k][j];
            }
        }
    }
    r.clone()
}

pub fn transpose(m: Vec<Vec<i64>>) -> Vec<Vec<i64>> {
    let n = m.clone().len();
    let mut r = make_matrix(n);
    for i in 0..n {
        for j in 0..n {
            r[j][i] = m[i][j];
        }
    }
    r.clone()
}

pub fn trace(m: Vec<Vec<i64>>) -> i64 {
    let mut t: i64 = 0;
    for i in 0..m.clone().len() {
        t = t + m[i][i];
    }
    t
}

pub fn sum_all(m: Vec<Vec<i64>>) -> i64 {
    let mut s: i64 = 0;
    for i in 0..m.clone().len() {
        for j in 0..m[i].clone().len() {
            s = s + m[i][j];
        }
    }
    s
}

pub fn big_calc(n: usize) -> String {
    let a = fill_matrix(make_matrix(n));
    let b = fill_matrix(make_matrix(n));
    let c = multiply(a.clone(), b.clone());
    let d = transpose(c.clone());
    let e = multiply(c.clone(), d.clone());
    format!("trace={} sum={}", trace(e.clone()), sum_all(e.clone()))
}
