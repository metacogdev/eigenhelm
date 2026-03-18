// copy-paste event handler registration with tiny variations
var handlers = {};

function on1(el, data) { handlers["click_1"] = function() { return data * 2 + 1; }; }
function on2(el, data) { handlers["click_2"] = function() { return data * 2 + 2; }; }
function on3(el, data) { handlers["click_3"] = function() { return data * 2 + 3; }; }
function on4(el, data) { handlers["click_4"] = function() { return data * 2 + 4; }; }
function on5(el, data) { handlers["click_5"] = function() { return data * 2 + 5; }; }
function on6(el, data) { handlers["click_6"] = function() { return data * 2 + 6; }; }
function on7(el, data) { handlers["click_7"] = function() { return data * 2 + 7; }; }
function on8(el, data) { handlers["click_8"] = function() { return data * 2 + 8; }; }
function on9(el, data) { handlers["click_9"] = function() { return data * 2 + 9; }; }
function on10(el, data) { handlers["click_10"] = function() { return data * 2 + 10; }; }

function setupAll(el, data) {
    on1(el, data);
    on2(el, data);
    on3(el, data);
    on4(el, data);
    on5(el, data);
    on6(el, data);
    on7(el, data);
    on8(el, data);
    on9(el, data);
    on10(el, data);
}

function trigger(name) {
    if (handlers[name] != undefined) {
        return handlers[name]();
    }
    return null;
}

function triggerAll() {
    var results = [];
    results.push(trigger("click_1"));
    results.push(trigger("click_2"));
    results.push(trigger("click_3"));
    results.push(trigger("click_4"));
    results.push(trigger("click_5"));
    results.push(trigger("click_6"));
    results.push(trigger("click_7"));
    results.push(trigger("click_8"));
    results.push(trigger("click_9"));
    results.push(trigger("click_10"));
    return results;
}
