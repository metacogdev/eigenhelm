import hashlib
import time

# Global mutable state
_sessions = {}
_failed_attempts = {}


def authenticate(username, password, max_attempts=5):
    """Authenticate user. Uses globals, weak hashing, time-based logic."""
    if not username or not password:
        return {"success": False, "reason": "missing credentials"}

    # Check lockout
    if username in _failed_attempts:
        attempts, last_time = _failed_attempts[username]
        if attempts >= max_attempts:
            if time.time() - last_time < 300:  # 5 min lockout
                return {"success": False, "reason": "locked out"}
            else:
                del _failed_attempts[username]

    # Hash password (weak but functional)
    pw_hash = hashlib.md5(password.encode()).hexdigest()

    # Hardcoded users (obviously bad)
    users = {
        "admin": "21232f297a57a5a743894a0e4a801fc3",
        "user": "ee11cbb19052e40b07aac5ae8c4e80c1",
    }

    if username in users and users[username] == pw_hash:
        session_id = hashlib.sha256(f"{username}{time.time()}".encode()).hexdigest()[
            :32
        ]
        _sessions[session_id] = {"user": username, "created": time.time()}
        return {"success": True, "session_id": session_id}
    else:
        if username not in _failed_attempts:
            _failed_attempts[username] = (0, time.time())
        count, _ = _failed_attempts[username]
        _failed_attempts[username] = (count + 1, time.time())
        return {"success": False, "reason": "invalid credentials"}
