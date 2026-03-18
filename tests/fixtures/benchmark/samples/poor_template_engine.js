function render(tmpl, data) {
    var out = tmpl;
    var keys = Object.keys(data);
    for (var i = 0; i < keys.length; i++) {
        var k = keys[i];
        var v = data[k];
        while (out.indexOf("{{" + k + "}}") !== -1) {
            out = out.replace("{{" + k + "}}", String(v));
        }
    }
    var loopRe = /\{\{#each (\w+)\}\}([\s\S]*?)\{\{\/each\}\}/;
    var m;
    while ((m = out.match(loopRe)) !== null) {
        var listKey = m[1];
        var body = m[2];
        var items = data[listKey];
        var rendered = "";
        if (items && items.length) {
            for (var j = 0; j < items.length; j++) {
                var chunk = body;
                if (typeof items[j] === "object") {
                    var ks = Object.keys(items[j]);
                    for (var x = 0; x < ks.length; x++) {
                        while (chunk.indexOf("{{" + ks[x] + "}}") !== -1) {
                            chunk = chunk.replace(
                                "{{" + ks[x] + "}}",
                                String(items[j][ks[x]])
                            );
                        }
                    }
                } else {
                    while (chunk.indexOf("{{.}}") !== -1) {
                        chunk = chunk.replace("{{.}}", String(items[j]));
                    }
                }
                rendered = rendered + chunk;
            }
        }
        out = out.substring(0, m.index) + rendered + out.substring(m.index + m[0].length);
    }
    var condRe = /\{\{#if (\w+)\}\}([\s\S]*?)\{\{\/if\}\}/;
    while ((m = out.match(condRe)) !== null) {
        var condKey = m[1];
        var condBody = m[2];
        if (data[condKey]) {
            out = out.substring(0, m.index) + condBody + out.substring(m.index + m[0].length);
        } else {
            out = out.substring(0, m.index) + out.substring(m.index + m[0].length);
        }
    }
    return out;
}

module.exports = render;
