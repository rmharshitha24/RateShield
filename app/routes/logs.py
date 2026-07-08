from flask import Blueprint, request

from app.services.log_service import LogService
from app.utils.responses import success_response

logs_bp = Blueprint("logs", __name__)


@logs_bp.get("/logs")
def get_logs():
    limit = request.args.get("limit", default=100, type=int)
    return success_response([log.to_dict() for log in LogService.list_logs(limit)])
