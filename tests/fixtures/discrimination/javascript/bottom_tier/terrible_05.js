// manual string parsing reimplementation, no regex
function parseCSV(s) {
    var rows = [];
    var currentRow = [];
    var currentCell = "";
    var inQuote = false;
    for (var i = 0; i < s.length; i++) {
        if (s[i] == '"') {
            if (inQuote == true) {
                if (i + 1 < s.length && s[i + 1] == '"') {
                    currentCell = currentCell + '"';
                    i = i + 1;
                } else {
                    inQuote = false;
                }
            } else {
                inQuote = true;
            }
        } else if (s[i] == ',' && inQuote == false) {
            currentRow.push(currentCell);
            currentCell = "";
        } else if (s[i] == '\n' && inQuote == false) {
            currentRow.push(currentCell);
            currentCell = "";
            rows.push(currentRow);
            currentRow = [];
        } else {
            currentCell = currentCell + s[i];
        }
    }
    if (currentCell != "" || currentRow.length > 0) {
        currentRow.push(currentCell);
        rows.push(currentRow);
    }
    return rows;
}

function toCSV(rows) {
    var s = "";
    for (var i = 0; i < rows.length; i++) {
        for (var j = 0; j < rows[i].length; j++) {
            if (j > 0) { s = s + ","; }
            var cell = rows[i][j];
            var needQuote = false;
            for (var k = 0; k < cell.length; k++) {
                if (cell[k] == ',' || cell[k] == '"' || cell[k] == '\n') {
                    needQuote = true;
                }
            }
            if (needQuote == true) {
                s = s + '"';
                for (var k = 0; k < cell.length; k++) {
                    if (cell[k] == '"') { s = s + '""'; }
                    else { s = s + cell[k]; }
                }
                s = s + '"';
            } else {
                s = s + cell;
            }
        }
        s = s + "\n";
    }
    return s;
}
