// manual number formatting, reimplemented padStart, string math
function padLeft(s, n, ch) {
    var r = s;
    while (r.length < n) {
        r = ch + r;
    }
    return r;
}

function padRight(s, n, ch) {
    var r = s;
    while (r.length < n) {
        r = r + ch;
    }
    return r;
}

function formatNumber(n) {
    var s = "" + n;
    var parts = s.split(".");
    var intPart = parts[0];
    var decPart = parts.length > 1 ? parts[1] : "";
    var negative = false;
    if (intPart[0] == "-") {
        negative = true;
        intPart = intPart.substring(1);
    }
    var formatted = "";
    var count = 0;
    for (var i = intPart.length - 1; i >= 0; i--) {
        formatted = intPart[i] + formatted;
        count = count + 1;
        if (count % 3 == 0 && i > 0) {
            formatted = "," + formatted;
        }
    }
    if (negative == true) {
        formatted = "-" + formatted;
    }
    if (decPart != "") {
        formatted = formatted + "." + decPart;
    }
    return formatted;
}

function formatCurrency(n) {
    var s = formatNumber(Math.floor(n * 100) / 100);
    var parts = s.split(".");
    if (parts.length == 1) {
        return "$" + s + ".00";
    } else if (parts[1].length == 1) {
        return "$" + s + "0";
    } else {
        return "$" + s;
    }
}

function formatPercent(n) {
    return formatNumber(Math.floor(n * 10000) / 100) + "%";
}

function repeat(s, n) {
    var r = "";
    for (var i = 0; i < n; i++) {
        r = r + s;
    }
    return r;
}

function center(s, w) {
    var pad = w - s.length;
    var left = Math.floor(pad / 2);
    var right = pad - left;
    return repeat(" ", left) + s + repeat(" ", right);
}
