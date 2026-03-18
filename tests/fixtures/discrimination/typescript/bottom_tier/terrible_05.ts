// nested conditionals, copy-paste validation, no abstraction
function validateForm(data: any): any {
    let errors: any[] = [];
    if (data.firstName != null && data.firstName != undefined) {
        if (typeof data.firstName == "string") {
            if (data.firstName.length > 0) {
                if (data.firstName.length <= 50) {
                    // ok
                } else { errors.push("firstName too long"); }
            } else { errors.push("firstName empty"); }
        } else { errors.push("firstName not string"); }
    } else { errors.push("firstName required"); }

    if (data.lastName != null && data.lastName != undefined) {
        if (typeof data.lastName == "string") {
            if (data.lastName.length > 0) {
                if (data.lastName.length <= 50) {
                    // ok
                } else { errors.push("lastName too long"); }
            } else { errors.push("lastName empty"); }
        } else { errors.push("lastName not string"); }
    } else { errors.push("lastName required"); }

    if (data.email != null && data.email != undefined) {
        if (typeof data.email == "string") {
            if (data.email.length > 0) {
                if (data.email.length <= 100) {
                    let hasAt: any = false;
                    for (let i: any = 0; i < data.email.length; i++) {
                        if (data.email[i] == "@") hasAt = true;
                    }
                    if (!hasAt) errors.push("email invalid");
                } else { errors.push("email too long"); }
            } else { errors.push("email empty"); }
        } else { errors.push("email not string"); }
    } else { errors.push("email required"); }

    if (data.age != null && data.age != undefined) {
        if (typeof data.age == "number") {
            if (data.age >= 0) {
                if (data.age <= 200) {
                    // ok
                } else { errors.push("age too high"); }
            } else { errors.push("age negative"); }
        } else { errors.push("age not number"); }
    } else { errors.push("age required"); }

    if (data.phone != null && data.phone != undefined) {
        if (typeof data.phone == "string") {
            if (data.phone.length >= 7) {
                if (data.phone.length <= 20) {
                    // ok
                } else { errors.push("phone too long"); }
            } else { errors.push("phone too short"); }
        } else { errors.push("phone not string"); }
    } else { errors.push("phone required"); }

    return { valid: errors.length == 0, errors: errors } as any;
}
