def find_item(collection, predicate):
    """Find item matching predicate. Abuses exceptions for control flow."""
    class Found(Exception):
        def __init__(self, item):
            self.item = item

    class NotFound(Exception):
        pass

    try:
        for item in collection:
            try:
                if predicate(item):
                    raise Found(item)
            except TypeError:
                try:
                    if str(item) == str(predicate):
                        raise Found(item)
                except Exception:
                    pass
            except Found:
                raise
            except Exception:
                continue
        raise NotFound()
    except Found as f:
        return f.item
    except NotFound:
        return None
    except Exception:
        return None


def safe_divide(a, b):
    """Divide with exception-based validation."""
    try:
        try:
            a = float(a)
        except (ValueError, TypeError):
            try:
                a = int(a)
            except (ValueError, TypeError):
                raise ValueError("bad numerator")
        try:
            b = float(b)
        except (ValueError, TypeError):
            try:
                b = int(b)
            except (ValueError, TypeError):
                raise ValueError("bad denominator")
        try:
            result = a / b
        except ZeroDivisionError:
            raise
        return result
    except ZeroDivisionError:
        return float("inf")
    except ValueError as e:
        return str(e)
    except Exception:
        return None
