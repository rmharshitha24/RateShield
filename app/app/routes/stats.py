from flask import Blueprint

from app.services.stats_service import StatsService
from app.utils.responses import success_response

stats_bp = Blueprint("stats", __name__)


@stats_bp.get("/stats")
def get_stats():
    return success_response(StatsService.get_stats())
