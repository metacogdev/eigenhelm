// deeply nested loops, magic numbers, unnecessary complexity
function matrix(n) {
    var m = [];
    for (var i = 0; i < n; i++) {
        m[i] = [];
        for (var j = 0; j < n; j++) {
            m[i][j] = 0;
        }
    }
    return m;
}

function fill(m) {
    for (var i = 0; i < m.length; i++) {
        for (var j = 0; j < m[i].length; j++) {
            m[i][j] = i * 17 + j * 13 + 7;
        }
    }
    return m;
}

function multiply(a, b) {
    var n = a.length;
    var r = matrix(n);
    for (var i = 0; i < n; i++) {
        for (var j = 0; j < n; j++) {
            for (var k = 0; k < n; k++) {
                r[i][j] = r[i][j] + a[i][k] * b[k][j];
            }
        }
    }
    return r;
}

function transpose(m) {
    var n = m.length;
    var r = matrix(n);
    for (var i = 0; i < n; i++) {
        for (var j = 0; j < n; j++) {
            r[j][i] = m[i][j];
        }
    }
    return r;
}

function trace(m) {
    var t = 0;
    for (var i = 0; i < m.length; i++) {
        t = t + m[i][i];
    }
    return t;
}

function sumAll(m) {
    var s = 0;
    for (var i = 0; i < m.length; i++) {
        for (var j = 0; j < m[i].length; j++) {
            s = s + m[i][j];
        }
    }
    return s;
}

function bigCalc(n) {
    var a = fill(matrix(n));
    var b = fill(matrix(n));
    var c = multiply(a, b);
    var d = transpose(c);
    var e = multiply(c, d);
    return trace(e) + sumAll(e);
}
