/**
 * Run async tasks with a concurrency limit.
 * Each task is a function returning a Promise.
 */
function promisePool(tasks, concurrency) {
    return new Promise(function (resolve, reject) {
        var results = new Array(tasks.length);
        var running = 0;
        var nextIndex = 0;
        var hasRejected = false;

        function runNext() {
            if (hasRejected) {
                return;
            }
            if (nextIndex >= tasks.length && running === 0) {
                resolve(results);
                return;
            }

            while (running < concurrency && nextIndex < tasks.length) {
                var currentIndex = nextIndex;
                nextIndex++;
                running++;

                var taskFn = tasks[currentIndex];
                Promise.resolve()
                    .then(function () {
                        return taskFn();
                    })
                    .then(function (result) {
                        results[currentIndex] = result;
                        running--;
                        runNext();
                    })
                    .catch(function (err) {
                        if (!hasRejected) {
                            hasRejected = true;
                            reject(err);
                        }
                    });
            }
        }

        if (tasks.length === 0) {
            resolve([]);
            return;
        }

        runNext();
    });
}

module.exports = promisePool;
