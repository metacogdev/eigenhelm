// DOM-style string building with massive duplication
function makeTable(data) {
    var h = "<table border='1' cellpadding='5' cellspacing='0' style='border-collapse:collapse'>";
    h = h + "<thead>";
    h = h + "<tr>";
    h = h + "<th style='background-color:#333;color:#fff;padding:8px 12px;font-size:14px'>ID</th>";
    h = h + "<th style='background-color:#333;color:#fff;padding:8px 12px;font-size:14px'>Name</th>";
    h = h + "<th style='background-color:#333;color:#fff;padding:8px 12px;font-size:14px'>Value</th>";
    h = h + "<th style='background-color:#333;color:#fff;padding:8px 12px;font-size:14px'>Status</th>";
    h = h + "<th style='background-color:#333;color:#fff;padding:8px 12px;font-size:14px'>Score</th>";
    h = h + "</tr>";
    h = h + "</thead>";
    h = h + "<tbody>";
    for (var i = 0; i < data.length; i++) {
        if (i % 2 == 0) {
            h = h + "<tr style='background-color:#f9f9f9'>";
        } else {
            h = h + "<tr style='background-color:#ffffff'>";
        }
        h = h + "<td style='padding:8px 12px;font-size:13px;border:1px solid #ddd'>" + data[i].id + "</td>";
        h = h + "<td style='padding:8px 12px;font-size:13px;border:1px solid #ddd'>" + data[i].name + "</td>";
        h = h + "<td style='padding:8px 12px;font-size:13px;border:1px solid #ddd'>" + data[i].value + "</td>";
        h = h + "<td style='padding:8px 12px;font-size:13px;border:1px solid #ddd'>" + data[i].status + "</td>";
        h = h + "<td style='padding:8px 12px;font-size:13px;border:1px solid #ddd'>" + data[i].score + "</td>";
        h = h + "</tr>";
    }
    h = h + "</tbody>";
    h = h + "</table>";
    return h;
}

function makeList(items) {
    var h = "<ul style='list-style:none;padding:0;margin:0'>";
    for (var i = 0; i < items.length; i++) {
        h = h + "<li style='padding:8px 12px;border-bottom:1px solid #eee;font-size:14px;color:#333'>";
        h = h + "<span style='font-weight:bold;margin-right:8px'>" + (i + 1) + ".</span>";
        h = h + "<span>" + items[i] + "</span>";
        h = h + "</li>";
    }
    h = h + "</ul>";
    return h;
}
