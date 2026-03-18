// reimplemented array methods, all var, == throughout
function myMap(arr, fn) {
    var result = [];
    for (var i = 0; i < arr.length; i++) {
        result.push(fn(arr[i], i));
    }
    return result;
}

function myFilter(arr, fn) {
    var result = [];
    for (var i = 0; i < arr.length; i++) {
        if (fn(arr[i], i) == true) {
            result.push(arr[i]);
        }
    }
    return result;
}

function myReduce(arr, fn, init) {
    var acc = init;
    for (var i = 0; i < arr.length; i++) {
        acc = fn(acc, arr[i], i);
    }
    return acc;
}

function myFind(arr, fn) {
    for (var i = 0; i < arr.length; i++) {
        if (fn(arr[i], i) == true) {
            return arr[i];
        }
    }
    return undefined;
}

function myEvery(arr, fn) {
    for (var i = 0; i < arr.length; i++) {
        if (fn(arr[i], i) == false) {
            return false;
        }
    }
    return true;
}

function mySome(arr, fn) {
    for (var i = 0; i < arr.length; i++) {
        if (fn(arr[i], i) == true) {
            return true;
        }
    }
    return false;
}

function mySort(arr) {
    var a = [];
    for (var i = 0; i < arr.length; i++) { a.push(arr[i]); }
    for (var i = 0; i < a.length; i++) {
        for (var j = 0; j < a.length - 1; j++) {
            if (a[j] > a[j + 1]) {
                var t = a[j];
                a[j] = a[j + 1];
                a[j + 1] = t;
            }
        }
    }
    return a;
}

function pipeline(arr) {
    var r = myFilter(arr, function(x) { return x > 0; });
    r = myMap(r, function(x) { return x * 2; });
    r = mySort(r);
    var sum = myReduce(r, function(a, x) { return a + x; }, 0);
    return sum;
}
