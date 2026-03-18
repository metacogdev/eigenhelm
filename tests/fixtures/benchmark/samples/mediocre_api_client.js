function apiClient(baseUrl) {
    var token = null;

    function request(method, path, body, callback) {
        var xhr = new XMLHttpRequest();
        xhr.open(method, baseUrl + path);
        xhr.setRequestHeader("Content-Type", "application/json");
        if (token) {
            xhr.setRequestHeader("Authorization", "Bearer " + token);
        }
        xhr.onreadystatechange = function () {
            if (xhr.readyState === 4) {
                if (xhr.status >= 200 && xhr.status < 300) {
                    try {
                        var parsed = JSON.parse(xhr.responseText);
                        callback(null, parsed);
                    } catch (e) {
                        callback(new Error("Bad JSON: " + e.message), null);
                    }
                } else if (xhr.status === 401) {
                    login(function (err) {
                        if (err) {
                            callback(err, null);
                        } else {
                            request(method, path, body, function (err2, data) {
                                if (err2) {
                                    callback(err2, null);
                                } else {
                                    callback(null, data);
                                }
                            });
                        }
                    });
                } else {
                    callback(new Error("HTTP " + xhr.status), null);
                }
            }
        };
        if (body) {
            xhr.send(JSON.stringify(body));
        } else {
            xhr.send();
        }
    }

    function login(callback) {
        var xhr = new XMLHttpRequest();
        xhr.open("POST", baseUrl + "/auth/refresh");
        xhr.onreadystatechange = function () {
            if (xhr.readyState === 4) {
                if (xhr.status === 200) {
                    try {
                        var data = JSON.parse(xhr.responseText);
                        token = data.token;
                        callback(null);
                    } catch (e) {
                        callback(new Error("Auth parse error"));
                    }
                } else {
                    callback(new Error("Auth failed: " + xhr.status));
                }
            }
        };
        xhr.send();
    }

    return {
        get: function (path, cb) { request("GET", path, null, cb); },
        post: function (path, body, cb) { request("POST", path, body, cb); },
        put: function (path, body, cb) { request("PUT", path, body, cb); },
        del: function (path, cb) { request("DELETE", path, null, cb); },
        setToken: function (t) { token = t; },
    };
}

module.exports = apiClient;
