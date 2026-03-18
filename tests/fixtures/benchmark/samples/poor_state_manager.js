var _state = {};
var _history = [];
var _mode = "normal";
var _locked = false;
var _count = 0;

function setState(k, v) {
    if (_locked) return;
    _history.push(JSON.parse(JSON.stringify(_state)));
    _state[k] = v;
    _count = _count + 1;
    if (_count > 100) {
        _history = _history.slice(_history.length - 50);
    }
}

function getState(k) {
    if (k) return _state[k];
    return _state;
}

function undo() {
    if (_locked) return false;
    if (_history.length > 0) {
        _state = _history.pop();
        return true;
    }
    return false;
}

function lock() { _locked = true; }
function unlock() { _locked = false; }

function setMode(m) {
    if (m === "strict" || m === "normal" || m === "debug") {
        _mode = m;
    }
}

function reset() {
    _state = {};
    _history = [];
    _mode = "normal";
    _locked = false;
    _count = 0;
}

function dump() {
    return {
        state: _state,
        history: _history,
        mode: _mode,
        locked: _locked,
        count: _count,
    };
}

function batchSet(pairs) {
    for (var i = 0; i < pairs.length; i++) {
        setState(pairs[i][0], pairs[i][1]);
    }
}

module.exports = {
    setState: setState,
    getState: getState,
    undo: undo,
    lock: lock,
    unlock: unlock,
    setMode: setMode,
    reset: reset,
    dump: dump,
    batchSet: batchSet,
};
