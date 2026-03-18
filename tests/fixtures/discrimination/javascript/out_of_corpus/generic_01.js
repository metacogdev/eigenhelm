function buildHtmlList(items) {
  var html = "<ul>";
  for (var i = 0; i < items.length; i++) {
    html += "<li>" + items[i] + "</li>";
  }
  html += "</ul>";
  return html;
}

function buildTable(headers, rows) {
  var html = "<table><tr>";
  for (var i = 0; i < headers.length; i++) {
    html += "<th>" + headers[i] + "</th>";
  }
  html += "</tr>";
  for (var r = 0; r < rows.length; r++) {
    html += "<tr>";
    for (var c = 0; c < rows[r].length; c++) {
      html += "<td>" + rows[r][c] + "</td>";
    }
    html += "</tr>";
  }
  html += "</table>";
  return html;
}
