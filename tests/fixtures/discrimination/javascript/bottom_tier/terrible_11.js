// manual date math, off-by-one paradise, magic numbers
function getDaysInMonth(m, y) {
    if (m == 1) return 31;
    if (m == 2) {
        if (y % 4 == 0) {
            if (y % 100 == 0) {
                if (y % 400 == 0) {
                    return 29;
                } else {
                    return 28;
                }
            } else {
                return 29;
            }
        } else {
            return 28;
        }
    }
    if (m == 3) return 31;
    if (m == 4) return 30;
    if (m == 5) return 31;
    if (m == 6) return 30;
    if (m == 7) return 31;
    if (m == 8) return 31;
    if (m == 9) return 30;
    if (m == 10) return 31;
    if (m == 11) return 30;
    if (m == 12) return 31;
    return -1;
}

function daysBetween(m1, d1, y1, m2, d2, y2) {
    var total = 0;
    var cm = m1;
    var cd = d1;
    var cy = y1;
    while (cy < y2 || (cy == y2 && cm < m2) || (cy == y2 && cm == m2 && cd < d2)) {
        cd = cd + 1;
        total = total + 1;
        if (cd > getDaysInMonth(cm, cy)) {
            cd = 1;
            cm = cm + 1;
            if (cm > 12) {
                cm = 1;
                cy = cy + 1;
            }
        }
    }
    return total;
}

function formatDate(m, d, y) {
    var ms = "";
    if (m < 10) { ms = "0" + m; } else { ms = "" + m; }
    var ds = "";
    if (d < 10) { ds = "0" + d; } else { ds = "" + d; }
    return ms + "/" + ds + "/" + y;
}

function addDays(m, d, y, n) {
    var cm = m;
    var cd = d;
    var cy = y;
    for (var i = 0; i < n; i++) {
        cd = cd + 1;
        if (cd > getDaysInMonth(cm, cy)) {
            cd = 1;
            cm = cm + 1;
            if (cm > 12) { cm = 1; cy = cy + 1; }
        }
    }
    return formatDate(cm, cd, cy);
}
