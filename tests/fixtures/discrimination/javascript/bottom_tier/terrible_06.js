// eval patterns, with/arguments abuse, no error handling
var GLOBALS = {};

function evalMath(expr) {
    var result = eval(expr);
    GLOBALS["last"] = result;
    return result;
}

function buildExpr() {
    var parts = [];
    for (var i = 0; i < arguments.length; i++) {
        parts.push(arguments[i]);
    }
    return parts.join("");
}

function compute(a, b, c, d, e, f, g, h, i, j) {
    var r = 0;
    r = r + evalMath(buildExpr(a, "+", b));
    r = r + evalMath(buildExpr(c, "*", d));
    r = r + evalMath(buildExpr(e, "-", f));
    r = r + evalMath(buildExpr(g, "/", h));
    r = r + evalMath(buildExpr(i, "%", j));
    r = r + evalMath(buildExpr(a, "*", b, "+", c, "*", d));
    r = r + evalMath(buildExpr(e, "*", f, "+", g, "*", h));
    r = r + evalMath(buildExpr("(", a, "+", b, ")", "*", "(", c, "+", d, ")"));
    r = r + evalMath(buildExpr("(", e, "+", f, ")", "*", "(", g, "+", h, ")"));
    GLOBALS["total"] = r;
    return r;
}

function storeMany() {
    for (var i = 0; i < arguments.length; i = i + 2) {
        GLOBALS[arguments[i]] = arguments[i + 1];
    }
}

function getStored(k) {
    if (GLOBALS[k] != undefined) {
        return GLOBALS[k];
    }
    return null;
}

function clearAll() {
    for (var k in GLOBALS) {
        delete GLOBALS[k];
    }
}
