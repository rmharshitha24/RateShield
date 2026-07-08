from flask import Blueprint, g, request

from app.utils.responses import success_response

protected_bp = Blueprint("protected", __name__)


@protected_bp.get("/protected")
def protected():
    user = g.rate_limit_user
    rule = g.rate_limit_rule
    return success_response(
        {
            "message": "Request allowed.",
            "user": {"id": user.id, "username": user.username, "plan": user.plan},
            "endpoint": request.path,
            "rate_limit": rule.to_dict(),
            "remaining": g.rate_limit_remaining,
        }
    )
