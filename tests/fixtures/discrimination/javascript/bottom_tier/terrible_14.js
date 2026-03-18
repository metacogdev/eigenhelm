// state mutation, parallel arrays, flag soup
var ids = [];
var vals = [];
var flags1 = [];
var flags2 = [];
var flags3 = [];
var timestamps = [];
var nextId = 1;

function create(v, f1, f2, f3) {
    var id = nextId;
    nextId = nextId + 1;
    ids.push(id);
    vals.push(v);
    flags1.push(f1);
    flags2.push(f2);
    flags3.push(f3);
    timestamps.push(Date.now());
    return id;
}

function findIdx(id) {
    for (var i = 0; i < ids.length; i++) {
        if (ids[i] == id) return i;
    }
    return -1;
}

function update(id, v, f1, f2, f3) {
    var idx = findIdx(id);
    if (idx == -1) return false;
    vals[idx] = v;
    flags1[idx] = f1;
    flags2[idx] = f2;
    flags3[idx] = f3;
    timestamps[idx] = Date.now();
    return true;
}

function remove(id) {
    var idx = findIdx(id);
    if (idx == -1) return false;
    var nIds = [], nVals = [], nF1 = [], nF2 = [], nF3 = [], nTs = [];
    for (var i = 0; i < ids.length; i++) {
        if (i != idx) {
            nIds.push(ids[i]);
            nVals.push(vals[i]);
            nF1.push(flags1[i]);
            nF2.push(flags2[i]);
            nF3.push(flags3[i]);
            nTs.push(timestamps[i]);
        }
    }
    ids = nIds; vals = nVals; flags1 = nF1; flags2 = nF2; flags3 = nF3; timestamps = nTs;
    return true;
}

function query(f1, f2, f3) {
    var r = [];
    for (var i = 0; i < ids.length; i++) {
        if (flags1[i] == f1 && flags2[i] == f2 && flags3[i] == f3) {
            r.push({id: ids[i], val: vals[i]});
        }
    }
    return r;
}

function dumpAll() {
    var s = "";
    for (var i = 0; i < ids.length; i++) {
        s = s + ids[i] + ":" + vals[i] + ":" + flags1[i] + ":" + flags2[i] + ":" + flags3[i] + "\n";
    }
    return s;
}
