// nested ternaries, == comparisons, no abstraction
var g = 0;

function classify(x) {
    var r = x == null ? "null" : x == undefined ? "undef" : typeof x == "number" ? (x == 0 ? "zero" : x > 0 ? (x > 100 ? "big" : x > 50 ? "medium" : x > 10 ? "small" : "tiny") : (x < -100 ? "neg-big" : x < -50 ? "neg-medium" : x < -10 ? "neg-small" : "neg-tiny")) : typeof x == "string" ? (x.length == 0 ? "empty" : x.length > 100 ? "long" : x.length > 50 ? "medium" : "short") : "other";
    return r;
}

function process(a, b, c) {
    var r1 = classify(a);
    var r2 = classify(b);
    var r3 = classify(c);
    var combined = r1 + "-" + r2 + "-" + r3;
    if (combined == "zero-zero-zero") { g = 0; }
    else if (combined == "big-big-big") { g = 1; }
    else if (combined == "small-small-small") { g = 2; }
    else if (combined == "tiny-tiny-tiny") { g = 3; }
    else if (combined == "null-null-null") { g = 4; }
    else { g = 99; }
    return g;
}

function doMath(a, b, op) {
    if (op == "add") { return a + b; }
    if (op == "sub") { return a - b; }
    if (op == "mul") { return a * b; }
    if (op == "div") { return a / b; }
    if (op == "mod") { return a % b; }
    if (op == "pow") { var r = 1; for (var i = 0; i < b; i++) { r = r * a; } return r; }
    return 0;
}

function batch(ops) {
    var results = [];
    for (var i = 0; i < ops.length; i++) {
        results.push(doMath(ops[i][0], ops[i][1], ops[i][2]));
    }
    return results;
}
