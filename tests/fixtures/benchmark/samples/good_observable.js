/**
 * Simple observable value with subscribe/notify pattern.
 */
function Observable(initialValue) {
    var currentValue = initialValue;
    var subscribers = [];

    function getValue() {
        return currentValue;
    }

    function setValue(newValue) {
        var oldValue = currentValue;
        currentValue = newValue;
        if (oldValue !== newValue) {
            notifyAll(newValue, oldValue);
        }
    }

    function subscribe(callback) {
        if (typeof callback !== "function") {
            throw new TypeError("Subscriber must be a function");
        }
        subscribers.push(callback);
        return function unsubscribe() {
            var idx = subscribers.indexOf(callback);
            if (idx >= 0) {
                subscribers.splice(idx, 1);
            }
        };
    }

    function notifyAll(newVal, oldVal) {
        for (var i = 0; i < subscribers.length; i++) {
            subscribers[i](newVal, oldVal);
        }
    }

    return {
        get: getValue,
        set: setValue,
        subscribe: subscribe,
    };
}

module.exports = Observable;
