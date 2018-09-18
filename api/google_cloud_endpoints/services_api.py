import endpoints

from endpoints import remote
from container import slow_service as slow_service_container
from container import analytics_service as analytics_service_container
from services.slow_service import request_handler as slow_service_handler
from services.analytics_service import request_handler as \
    analytics_service_handler


@endpoints.api(name="service",
               version="v1",
               api_key_required=False,
               title="Services API")
class ServicesApi(remote.Service):
    """Services API deployed with Google Cloud Endpoints."""

    @endpoints.method(
        slow_service_container.get_content_name_request_type(),
        slow_service_container.get_content_name_response_type(),
        path="slowservice/content/{contentId}/detail",
        http_method="GET",
        name="slowServiceGetContentName")
    def slow_service_get_content_name(self, request):
        """Slow Service - getContentName - GET request"""

        response = slow_service_handler.get_content_name(request.contentId)
        return slow_service_container.build_get_content_name_response(response)

    @endpoints.method(
        analytics_service_container.add_event_request_type(),
        analytics_service_container.add_event_response_type(),
        path="analyticsservice/{customerId}/event",
        http_method="POST",
        name="analyticsServiceAddEvent")
    def analytics_service_add_event(self, request):
        """Analytics Service - addEvent - POST request"""

        # do authentication check via endpoints.get_current_user()
        user = request.user_info
        response = analytics_service_handler.add_event(
            request.customerId, request.content_id, request.time, user.ip,
            user.user_agent, user.location)
        return analytics_service_container.build_add_event_response(response)


api = endpoints.api_server([ServicesApi])
