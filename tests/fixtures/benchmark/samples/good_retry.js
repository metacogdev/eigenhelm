/**
 * Retry an async function with exponential backoff.
 */
function retry(fn, options) {
    var maxAttempts = (options && options.maxAttempts) || 3;
    var baseDelay = (options && options.baseDelay) || 100;
    var maxDelay = (options && options.maxDelay) || 5000;

    return new Promise(function (resolve, reject) {
        var attempt = 0;

        function tryOnce() {
            attempt++;
            Promise.resolve()
                .then(function () {
                    return fn(attempt);
                })
                .then(function (result) {
                    resolve(result);
                })
                .catch(function (err) {
                    if (attempt >= maxAttempts) {
                        reject(err);
                        return;
                    }
                    var delay = Math.min(
                        baseDelay * Math.pow(2, attempt - 1),
                        maxDelay
                    );
                    var jitter = Math.random() * delay * 0.1;
                    setTimeout(function () {
                        tryOnce();
                    }, delay + jitter);
                });
        }

        tryOnce();
    });
}

module.exports = retry;
