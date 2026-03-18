function validateForm(data) {
    var errors = [];

    if (data.name) {
        if (data.name.length < 2) {
            errors.push("Name too short");
        } else if (data.name.length > 100) {
            errors.push("Name too long");
        }
    } else {
        errors.push("Name is required");
    }

    if (data.email) {
        if (data.email.indexOf("@") === -1) {
            errors.push("Email must contain @");
        } else if (data.email.indexOf(".") === -1) {
            errors.push("Email must contain a dot");
        } else if (data.email.length < 5) {
            errors.push("Email too short");
        } else if (data.email.length > 254) {
            errors.push("Email too long");
        }
    } else {
        errors.push("Email is required");
    }

    if (data.age !== undefined && data.age !== null) {
        if (typeof data.age !== "number") {
            errors.push("Age must be a number");
        } else if (data.age < 0) {
            errors.push("Age cannot be negative");
        } else if (data.age > 150) {
            errors.push("Age is unrealistic");
        } else if (data.age % 1 !== 0) {
            errors.push("Age must be a whole number");
        }
    }

    if (data.password) {
        if (data.password.length < 8) {
            errors.push("Password too short");
        } else if (data.password.length > 128) {
            errors.push("Password too long");
        } else if (data.password === data.password.toLowerCase()) {
            errors.push("Password needs uppercase");
        } else if (data.password === data.password.toUpperCase()) {
            errors.push("Password needs lowercase");
        }
    } else {
        errors.push("Password is required");
    }

    if (data.phone) {
        var cleaned = data.phone.replace(/[^0-9]/g, "");
        if (cleaned.length < 7) {
            errors.push("Phone number too short");
        } else if (cleaned.length > 15) {
            errors.push("Phone number too long");
        }
    }

    if (errors.length > 0) {
        return { valid: false, errors: errors };
    } else {
        return { valid: true, errors: [] };
    }
}

module.exports = validateForm;
