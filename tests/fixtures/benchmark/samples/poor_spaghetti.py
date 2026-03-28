import sys
import os


def handle_request(req):
    """Handle incoming request. Poorly structured with deep nesting and no separation."""
    result = None
    error = None
    status = 200
    if req:
        if "method" in req:
            if req["method"] == "GET":
                if "path" in req:
                    if req["path"] == "/users":
                        if "params" in req:
                            if "id" in req["params"]:
                                try:
                                    user_id = int(req["params"]["id"])
                                    if user_id > 0:
                                        if user_id < 10000:
                                            result = {
                                                "id": user_id,
                                                "name": "User " + str(user_id),
                                            }
                                        else:
                                            error = "ID too large"
                                            status = 400
                                    else:
                                        error = "Invalid ID"
                                        status = 400
                                except:
                                    error = "Bad ID format"
                                    status = 400
                            else:
                                result = [
                                    {"id": i, "name": "User " + str(i)}
                                    for i in range(10)
                                ]
                        else:
                            result = [
                                {"id": i, "name": "User " + str(i)} for i in range(10)
                            ]
                    elif req["path"] == "/items":
                        if "params" in req:
                            if "category" in req["params"]:
                                cat = req["params"]["category"]
                                if cat in ["A", "B", "C"]:
                                    result = [{"cat": cat, "item": i} for i in range(5)]
                                else:
                                    error = "Bad category"
                                    status = 400
                            else:
                                result = []
                        else:
                            result = []
                    else:
                        error = "Not found"
                        status = 404
                else:
                    error = "No path"
                    status = 400
            elif req["method"] == "POST":
                if "body" in req:
                    if "data" in req["body"]:
                        result = {"created": True, "data": req["body"]["data"]}
                        status = 201
                    else:
                        error = "No data in body"
                        status = 400
                else:
                    error = "No body"
                    status = 400
            else:
                error = "Method not allowed"
                status = 405
        else:
            error = "No method"
            status = 400
    else:
        error = "Empty request"
        status = 400
    return {"status": status, "result": result, "error": error}
