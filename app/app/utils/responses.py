from flask import jsonify


def success_response(data: dict | list | None = None, status_code: int = 200):
    payload = {"success": True, "data": data if data is not None else {}}
    return jsonify(payload), status_code


def error_response(message: str, status_code: int, error: str = "error", headers: dict | None = None):
    response = jsonify({"success": False, "error": {"type": error, "message": message}})
    response.status_code = status_code
    if headers:
        for key, value in headers.items():
            response.headers[key] = value
    return response
