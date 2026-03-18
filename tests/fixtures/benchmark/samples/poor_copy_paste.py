def process_user(user_data):
    """Process user data. Heavy copy-paste duplication."""
    result = {}

    if "name" in user_data:
        name = user_data["name"]
        if isinstance(name, str):
            name = name.strip()
            if len(name) > 0:
                if len(name) <= 100:
                    result["name"] = name
                else:
                    result["name"] = name[:100]
                    result["name_error"] = "truncated"
            else:
                result["name"] = "Unknown"
                result["name_error"] = "empty"
        else:
            result["name"] = str(name)
            result["name_error"] = "converted"
    else:
        result["name"] = "Unknown"
        result["name_error"] = "missing"

    if "email" in user_data:
        email = user_data["email"]
        if isinstance(email, str):
            email = email.strip()
            if len(email) > 0:
                if len(email) <= 254:
                    result["email"] = email
                else:
                    result["email"] = email[:254]
                    result["email_error"] = "truncated"
            else:
                result["email"] = ""
                result["email_error"] = "empty"
        else:
            result["email"] = str(email)
            result["email_error"] = "converted"
    else:
        result["email"] = ""
        result["email_error"] = "missing"

    if "phone" in user_data:
        phone = user_data["phone"]
        if isinstance(phone, str):
            phone = phone.strip()
            if len(phone) > 0:
                if len(phone) <= 20:
                    result["phone"] = phone
                else:
                    result["phone"] = phone[:20]
                    result["phone_error"] = "truncated"
            else:
                result["phone"] = ""
                result["phone_error"] = "empty"
        else:
            result["phone"] = str(phone)
            result["phone_error"] = "converted"
    else:
        result["phone"] = ""
        result["phone_error"] = "missing"

    if "age" in user_data:
        age = user_data["age"]
        if isinstance(age, int):
            if age >= 0:
                if age <= 150:
                    result["age"] = age
                else:
                    result["age"] = 150
                    result["age_error"] = "capped"
            else:
                result["age"] = 0
                result["age_error"] = "negative"
        else:
            try:
                result["age"] = int(age)
            except (ValueError, TypeError):
                result["age"] = 0
                result["age_error"] = "invalid"
    else:
        result["age"] = 0
        result["age_error"] = "missing"

    return result
