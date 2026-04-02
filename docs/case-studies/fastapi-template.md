# Case Study: FastAPI Full-Stack Template

We ran eigenhelm against the [official FastAPI full-stack template](https://github.com/fastapi/full-stack-fastapi-template) to see what its structural analysis produces on real-world, human-authored Python.

## Reproducibility

| Parameter | Value |
|-----------|-------|
| Template | [`fastapi/full-stack-fastapi-template`](https://github.com/fastapi/full-stack-fastapi-template) |
| Commit | [`8bf0025`](https://github.com/fastapi/full-stack-fastapi-template/commit/8bf00250399b18b03247a02518275de626c83238) |
| eigenhelm version | 0.7.0 |
| Model | `general-polyglot-v1` (bundled default, 36 PCA components, 8228 training vectors from 1483 files across 5 languages) |
| Command | `eh evaluate backend/app/ --rank` |

To reproduce these results exactly:

```bash
uv tool install eigenhelm==0.7.0
git clone https://github.com/fastapi/full-stack-fastapi-template.git
cd full-stack-fastapi-template
git checkout 8bf0025
eh evaluate backend/app/ --rank
```

## Raw results

27 files evaluated:

| Score range | Count | Classification |
|-------------|-------|----------------|
| accept (< 0.4) | 4 | Empty `__init__.py` files (score 0.00) |
| marginal (0.4 – 0.6) | 3 | `security.py`, `config.py`, `routes/utils.py` |
| reject (≥ 0.6) | 20 | Most application code |

Bottom 5 by score:

```
* #23  backend/app/api/main.py                0.76  p11
* #24  backend/app/initial_data.py            0.77  p10
* #25  backend/app/alembic/env.py             0.77  p10  ← bottom
* #26  backend/app/api/routes/private.py      0.85  p5   ← bottom
* #27  backend/app/utils.py                   0.89  p2   ← bottom
```

## Observations

We looked at the three lowest-scoring files to understand what eigenhelm's directives pointed to.

### `utils.py` (score: 0.89, p2)

eigenhelm output:

```
backend/app/utils.py
  decision: reject
  score:    0.89 (p2 — better than 2% of training corpus)
  confidence: high
  contributions:
    manifold_drift           0.30  (weight: 0.30, normalized: 0.99)
    manifold_alignment       0.30  (weight: 0.30, normalized: 1.00)
    token_entropy            0.06  (weight: 0.15, normalized: 0.39)
    compression_structure    0.14  (weight: 0.15, normalized: 0.93)
    ncd_exemplar_distance    0.10  (weight: 0.10, normalized: 0.96)
  directives:
    [high] extract_repeated_logic → EmailData (lines 20-22)
      #1 wl_hash_bin_42: contribution=-1.60, deviation=+1.6σ
    [high] extract_repeated_logic → EmailData (lines 20-22)
      #1 wl_hash_bin_61: contribution=+5.41, deviation=+5.0σ
    [high] improve_compression → <source> (lines 1-123)
    [high] review_structure → <source> (lines 1-123)
```

**What eigenhelm flagged:** High manifold drift (normalized 0.99) and alignment (1.00), meaning this file's structural fingerprint is far from the training manifold along its principal axes. The `wl_hash_bin_61` deviation of +5.0σ indicates dramatically more repetition of a particular AST subtree shape than the model expects.

**What the code looks like:** The file contains three concerns — email rendering/sending, email template generation, and JWT token management. The three `generate_*_email` functions have near-identical AST structure: each gets the project name, builds a subject string, calls `render_email_template` with a context dict, and returns `EmailData`. The `send_email` function has a conditional chain building SMTP options (`if settings.SMTP_TLS`, `elif settings.SMTP_SSL`, `if settings.SMTP_USER`, `if settings.SMTP_PASSWORD`).

**Our interpretation:** The mixed concerns and repeated function shapes are real structural patterns that most experienced reviewers would notice. Whether they'd *fix* them in a template is a different question — templates often prioritize readability over structural elegance.

### `api/routes/private.py` (score: 0.85, p5)

eigenhelm output:

```
backend/app/api/routes/private.py
  decision: reject
  score:    0.85 (p5 — better than 5% of training corpus)
  confidence: high
  contributions:
    manifold_drift           0.29  (weight: 0.30, normalized: 0.98)
    manifold_alignment       0.27  (weight: 0.30, normalized: 0.91)
    token_entropy            0.06  (weight: 0.15, normalized: 0.42)
    compression_structure    0.13  (weight: 0.15, normalized: 0.90)
    ncd_exemplar_distance    0.09  (weight: 0.10, normalized: 0.90)
  directives:
    [high] extract_repeated_logic → PrivateUserCreate (lines 16-20)
    [medium] improve_compression → <source> (lines 1-38)
    [medium] review_structure → <source> (lines 1-38)
```

**What eigenhelm flagged:** High drift and alignment scores on a 38-line file.

**What the code looks like:** One Pydantic model, one route handler. That's the entire file.

**Our interpretation:** This is a limitation of file-level scoring on very small modules. There isn't enough structural content for the WL hash to capture meaningful patterns. The high drift reflects distance from the training manifold, which is expected when a file contains so little code. eigenhelm is technically correct — this file is structurally unlike the training corpus — but the observation isn't actionable.

### `models.py` (score: 0.75, p14)

eigenhelm output:

```
backend/app/models.py
  decision: reject
  score:    0.75 (p14 — better than 14% of training corpus)
  contributions:
    manifold_drift           0.24  (weight: 0.30, normalized: 0.79)
    manifold_alignment       0.21  (weight: 0.30, normalized: 0.71)
    compression_structure    0.14  (weight: 0.15, normalized: 0.94)
    ncd_exemplar_distance    0.10  (weight: 0.10, normalized: 0.96)
  directives:
    [high] extract_repeated_logic → get_datetime_utc (lines 9-10)
    [high] improve_compression → <source> (lines 1-129)
    [high] review_structure → <source> (lines 1-129)
```

**What eigenhelm flagged:** High compression structure score (0.94 normalized) — low structural regularity. The file has 13 SQLModel class definitions with repeated `Field(...)` patterns.

**What the code looks like:** Data model declarations — `UserBase`, `UserCreate`, `UserRegister`, `UserUpdate`, `ItemBase`, `ItemCreate`, `ItemUpdate`, plus response and token models. The repetition is inherent to the domain.

**Our interpretation:** eigenhelm correctly identifies that this file has high structural repetition. But the repetition is intentional — these are data transfer objects, and repeating field declarations is the standard SQLModel/Pydantic pattern. This is a case where the measurement is accurate but the appropriate response is to note it, not fix it.

## Refactor experiment

We tested whether splitting `utils.py` by concern would affect scores. The change: move the two JWT functions (`generate_password_reset_token`, `verify_password_reset_token`) into a new `tokens.py` module. No logic changes, just file reorganization.

The diff:

```diff
--- /dev/null
+++ b/backend/app/tokens.py
@@ -0,0 +1,30 @@
+from datetime import datetime, timedelta, timezone
+
+import jwt
+from jwt.exceptions import InvalidTokenError
+
+from app.core import security
+from app.core.config import settings
+
+
+def generate_password_reset_token(email: str) -> str:
+    delta = timedelta(hours=settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS)
+    now = datetime.now(timezone.utc)
+    expires = now + delta
+    exp = expires.timestamp()
+    encoded_jwt = jwt.encode(
+        {"exp": exp, "nbf": now, "sub": email},
+        settings.SECRET_KEY,
+        algorithm=security.ALGORITHM,
+    )
+    return encoded_jwt
+
+
+def verify_password_reset_token(token: str) -> str | None:
+    try:
+        decoded_token = jwt.decode(
+            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
+        )
+        return str(decoded_token["sub"])
+    except InvalidTokenError:
+        return None
```

To reproduce the experiment: check out commit `8bf0025`, create `tokens.py` with the content above, remove the two token functions from `utils.py` (rename the remainder to `email.py`), then run:

```bash
eh evaluate backend/app/email.py backend/app/tokens.py --classify
```

Results after the split:

| File | Before | After | Change |
|------|--------|-------|--------|
| `utils.py` (original) | 0.89 (p2) | — | Split into two files |
| `tokens.py` (new) | — | 0.59 (p59) | Marginal |
| `email.py` (remaining) | — | 0.89 (p3) | Still reject |

`tokens.py` scored 0.59 — marginal, better than 59% of the training corpus. Two focused, related functions with clean imports.

`email.py` (the remaining email code) stayed at 0.89. The structural repetition in the email generators and the SMTP conditional chain are still present. eigenhelm continues to flag them, and that assessment is defensible — the code *is* structurally repetitive.

## What we take from this

**What the tool measured correctly.** eigenhelm identified the mixed concerns in `utils.py` and the repeated AST structure in the email generators. These are patterns that many reviewers would flag. The `tokens.py` split produced a 0.30-point score improvement (0.89 → 0.59) by separating unrelated functionality — a standard refactoring that eigenhelm's directives pointed toward.

**Where the tool's measurement wasn't actionable.** `private.py` scored reject on a 38-line file — the module was too small for meaningful structural fingerprinting. `models.py` scored reject on intentionally repetitive data declarations. Both measurements are technically accurate but don't lead to useful changes.

**What didn't move.** The email code stayed at 0.89 after the split because the structural repetition is in the email generators themselves, not in the module organization. A deeper refactor — making the generators data-driven — might reduce the score, but that's a design decision with tradeoffs beyond what a scoring tool should prescribe.

## Try it

```bash
uv tool install eigenhelm
git clone https://github.com/fastapi/full-stack-fastapi-template.git
eh evaluate full-stack-fastapi-template/backend/app/ --rank
```
