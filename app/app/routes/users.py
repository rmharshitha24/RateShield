from flask import Blueprint, current_app, request

from app.services.user_service import UserService
from app.utils.responses import success_response

users_bp = Blueprint("users", __name__)


def _default_rule_config() -> dict:
    return {
        "algorithm": current_app.config["DEFAULT_RATE_LIMIT_ALGORITHM"],
        "max_requests": current_app.config["DEFAULT_MAX_REQUESTS"],
        "time_window": current_app.config["DEFAULT_TIME_WINDOW"],
        "refill_rate": current_app.config["DEFAULT_REFILL_RATE"],
        "bucket_capacity": current_app.config["DEFAULT_BUCKET_CAPACITY"],
    }


@users_bp.post("/users")
def create_user():
    user = UserService.create_user(request.get_json(silent=True) or {}, _default_rule_config())
    return success_response(user.to_dict(), 201)


@users_bp.get("/users")
def list_users():
    return success_response([user.to_dict() for user in UserService.list_users()])


@users_bp.get("/users/<int:user_id>")
def get_user(user_id: int):
    return success_response(UserService.get_user(user_id).to_dict())


@users_bp.put("/users/<int:user_id>/rate-limit")
def update_rate_limit(user_id: int):
    rule = UserService.upsert_rate_limit(user_id, request.get_json(silent=True) or {})
    return success_response(rule.to_dict())


@users_bp.delete("/users/<int:user_id>")
def delete_user(user_id: int):
    UserService.delete_user(user_id)
    return success_response({"deleted": True})
