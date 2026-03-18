/**
 * Creates a debounced version of the given function that delays
 * invocation until after `wait` milliseconds of inactivity.
 *
 * Returns the debounced function with a `.cancel()` method.
 */
function debounce(fn, wait) {
    let timerId = null;

    function debounced(...args) {
        if (timerId !== null) {
            clearTimeout(timerId);
        }
        timerId = setTimeout(() => {
            timerId = null;
            fn.apply(this, args);
        }, wait);
    }

    debounced.cancel = function () {
        if (timerId !== null) {
            clearTimeout(timerId);
            timerId = null;
        }
    };

    debounced.pending = function () {
        return timerId !== null;
    };

    return debounced;
}

module.exports = debounce;
