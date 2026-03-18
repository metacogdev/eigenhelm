// giant switch statement, string concatenation for HTML, var everywhere
var output = "";

function render(type, a, b, c, d) {
    var html = "";
    switch(type) {
        case 1: html = "<div class='t1'>" + "<span>" + a + "</span>" + "<span>" + b + "</span>" + "</div>"; break;
        case 2: html = "<div class='t2'>" + "<span>" + a + "</span>" + "<span>" + b + "</span>" + "</div>"; break;
        case 3: html = "<div class='t3'>" + "<span>" + a + "</span>" + "<span>" + b + "</span>" + "</div>"; break;
        case 4: html = "<div class='t4'>" + "<span>" + a + "</span>" + "<span>" + b + "</span>" + "</div>"; break;
        case 5: html = "<div class='t5'>" + "<span>" + a + "</span>" + "<span>" + b + "</span>" + "</div>"; break;
        case 6: html = "<div class='t6'>" + "<span>" + a + "</span>" + "<span>" + c + "</span>" + "</div>"; break;
        case 7: html = "<div class='t7'>" + "<span>" + a + "</span>" + "<span>" + c + "</span>" + "</div>"; break;
        case 8: html = "<div class='t8'>" + "<span>" + a + "</span>" + "<span>" + c + "</span>" + "</div>"; break;
        case 9: html = "<div class='t9'>" + "<span>" + a + "</span>" + "<span>" + d + "</span>" + "</div>"; break;
        case 10: html = "<div class='t10'>" + "<span>" + a + "</span>" + "<span>" + d + "</span>" + "</div>"; break;
        case 11: html = "<div class='t11'>" + "<span>" + b + "</span>" + "<span>" + c + "</span>" + "</div>"; break;
        case 12: html = "<div class='t12'>" + "<span>" + b + "</span>" + "<span>" + d + "</span>" + "</div>"; break;
        case 13: html = "<div class='t13'>" + "<span>" + c + "</span>" + "<span>" + d + "</span>" + "</div>"; break;
        case 14: html = "<div class='t14'>" + "<span>" + a + "</span>" + "<span>" + b + "</span>" + "<span>" + c + "</span>" + "</div>"; break;
        case 15: html = "<div class='t15'>" + "<span>" + a + "</span>" + "<span>" + b + "</span>" + "<span>" + c + "</span>" + "<span>" + d + "</span>" + "</div>"; break;
        default: html = "<div class='unknown'>" + a + "</div>"; break;
    }
    output = output + html;
    return html;
}

function renderAll(items) {
    var result = "<html><body>";
    for (var i = 0; i < items.length; i++) {
        result = result + render(items[i].type, items[i].a, items[i].b, items[i].c, items[i].d);
    }
    result = result + "</body></html>";
    return result;
}
