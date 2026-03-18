// manual char counting, if-else chain, no iteration patterns
pub fn count_chars(s: String) -> Vec<(String, i32)> {
    let mut ca = 0; let mut cb = 0; let mut cc = 0; let mut cd = 0;
    let mut ce = 0; let mut cf = 0; let mut cg = 0; let mut ch = 0;
    let mut ci = 0; let mut cj = 0; let mut ck = 0; let mut cl = 0;
    let mut cm = 0; let mut cn = 0; let mut co = 0; let mut cp = 0;
    let mut cq = 0; let mut cr = 0; let mut cs = 0; let mut ct = 0;
    let mut cu = 0; let mut cv = 0; let mut cw = 0; let mut cx = 0;
    let mut cy = 0; let mut cz = 0;
    for c in s.clone().chars() {
        if c == 'a' { ca = ca + 1; }
        else if c == 'b' { cb = cb + 1; }
        else if c == 'c' { cc = cc + 1; }
        else if c == 'd' { cd = cd + 1; }
        else if c == 'e' { ce = ce + 1; }
        else if c == 'f' { cf = cf + 1; }
        else if c == 'g' { cg = cg + 1; }
        else if c == 'h' { ch = ch + 1; }
        else if c == 'i' { ci = ci + 1; }
        else if c == 'j' { cj = cj + 1; }
        else if c == 'k' { ck = ck + 1; }
        else if c == 'l' { cl = cl + 1; }
        else if c == 'm' { cm = cm + 1; }
        else if c == 'n' { cn = cn + 1; }
        else if c == 'o' { co = co + 1; }
        else if c == 'p' { cp = cp + 1; }
        else if c == 'q' { cq = cq + 1; }
        else if c == 'r' { cr = cr + 1; }
        else if c == 's' { cs = cs + 1; }
        else if c == 't' { ct = ct + 1; }
        else if c == 'u' { cu = cu + 1; }
        else if c == 'v' { cv = cv + 1; }
        else if c == 'w' { cw = cw + 1; }
        else if c == 'x' { cx = cx + 1; }
        else if c == 'y' { cy = cy + 1; }
        else if c == 'z' { cz = cz + 1; }
    }
    let mut r: Vec<(String, i32)> = Vec::new();
    r.push((String::from("a"), ca)); r.push((String::from("b"), cb));
    r.push((String::from("c"), cc)); r.push((String::from("d"), cd));
    r.push((String::from("e"), ce)); r.push((String::from("f"), cf));
    r.push((String::from("g"), cg)); r.push((String::from("h"), ch));
    r.push((String::from("i"), ci)); r.push((String::from("j"), cj));
    r.push((String::from("k"), ck)); r.push((String::from("l"), cl));
    r.push((String::from("m"), cm)); r.push((String::from("n"), cn));
    r.push((String::from("o"), co)); r.push((String::from("p"), cp));
    r.push((String::from("q"), cq)); r.push((String::from("r"), cr));
    r.push((String::from("s"), cs)); r.push((String::from("t"), ct));
    r.push((String::from("u"), cu)); r.push((String::from("v"), cv));
    r.push((String::from("w"), cw)); r.push((String::from("x"), cx));
    r.push((String::from("y"), cy)); r.push((String::from("z"), cz));
    r.clone()
}
