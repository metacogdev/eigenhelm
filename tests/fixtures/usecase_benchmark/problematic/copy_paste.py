"""Copy-paste duplication — known code smell."""


def process_users(users):
    results = []
    for user in users:
        if user.get("active"):
            name = user.get("name", "unknown")
            email = user.get("email", "unknown")
            role = user.get("role", "user")
            results.append({"name": name, "email": email, "role": role, "type": "user"})
    return results


def process_admins(admins):
    results = []
    for admin in admins:
        if admin.get("active"):
            name = admin.get("name", "unknown")
            email = admin.get("email", "unknown")
            role = admin.get("role", "admin")
            results.append(
                {"name": name, "email": email, "role": role, "type": "admin"}
            )
    return results


def process_guests(guests):
    results = []
    for guest in guests:
        if guest.get("active"):
            name = guest.get("name", "unknown")
            email = guest.get("email", "unknown")
            role = guest.get("role", "guest")
            results.append(
                {"name": name, "email": email, "role": role, "type": "guest"}
            )
    return results


def process_moderators(moderators):
    results = []
    for mod in moderators:
        if mod.get("active"):
            name = mod.get("name", "unknown")
            email = mod.get("email", "unknown")
            role = mod.get("role", "moderator")
            results.append(
                {"name": name, "email": email, "role": role, "type": "moderator"}
            )
    return results
