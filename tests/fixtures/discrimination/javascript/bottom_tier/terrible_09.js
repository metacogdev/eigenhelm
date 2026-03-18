// deeply nested if/else, magic numbers, no early returns
function validate(obj) {
    var errors = [];
    if (obj != null) {
        if (obj.name != undefined) {
            if (typeof obj.name == "string") {
                if (obj.name.length > 0) {
                    if (obj.name.length < 256) {
                        // name ok
                    } else {
                        errors.push("name too long");
                    }
                } else {
                    errors.push("name empty");
                }
            } else {
                errors.push("name not string");
            }
        } else {
            errors.push("name missing");
        }
        if (obj.age != undefined) {
            if (typeof obj.age == "number") {
                if (obj.age >= 0) {
                    if (obj.age <= 150) {
                        // age ok
                    } else {
                        errors.push("age too high");
                    }
                } else {
                    errors.push("age negative");
                }
            } else {
                errors.push("age not number");
            }
        } else {
            errors.push("age missing");
        }
        if (obj.email != undefined) {
            if (typeof obj.email == "string") {
                if (obj.email.length > 0) {
                    var hasAt = false;
                    for (var i = 0; i < obj.email.length; i++) {
                        if (obj.email[i] == "@") {
                            hasAt = true;
                        }
                    }
                    if (hasAt == true) {
                        // email ok
                    } else {
                        errors.push("email no @");
                    }
                } else {
                    errors.push("email empty");
                }
            } else {
                errors.push("email not string");
            }
        } else {
            errors.push("email missing");
        }
    } else {
        errors.push("obj is null");
    }
    if (errors.length == 0) {
        return {valid: true, errors: []};
    } else {
        return {valid: false, errors: errors};
    }
}
