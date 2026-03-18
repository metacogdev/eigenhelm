// callback hell with var and == everywhere
var data = [];
var count = 0;
var flag = false;

function doStuff(a, b, c, d, e, f, g, h, callback) {
    var r = 0;
    setTimeout(function() {
        r = a + b;
        setTimeout(function() {
            r = r + c + d;
            setTimeout(function() {
                r = r + e + f;
                setTimeout(function() {
                    r = r + g + h;
                    setTimeout(function() {
                        if (r == 0) {
                            data.push("zero");
                        } else if (r == 1) {
                            data.push("one");
                        } else if (r == 2) {
                            data.push("two");
                        } else if (r == 3) {
                            data.push("three");
                        } else {
                            data.push("other");
                        }
                        count = count + 1;
                        flag = true;
                        callback(r);
                    }, 0);
                }, 0);
            }, 0);
        }, 0);
    }, 0);
}

function processAll(items, callback) {
    var i = 0;
    var results = [];
    function next() {
        if (i < items.length) {
            doStuff(items[i], items[i], items[i], items[i], items[i], items[i], items[i], items[i], function(r) {
                results.push(r);
                i = i + 1;
                next();
            });
        } else {
            callback(results);
        }
    }
    next();
}
