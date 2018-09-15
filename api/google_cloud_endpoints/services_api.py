import endpoints

from endpoints import remote
from container import slow_service as slow_service_container
from services.slow_service import request_handler as slow_service_handler


@endpoints.api(name="service",
               version="v1",
               api_key_required=False,
               title="Services API")
class ServicesApi(remote.Service):

    @endpoints.method(
        slow_service_container.get_content_name_request_type(),
        slow_service_container.get_content_name_response_type(),
        path="slowservice/content/{contentId}/detail",
        http_method="GET",
        name="slowServiceGetContentName")
    def slow_service_get_content_name(self, request):
        content_name = slow_service_handler.get_content_name(request.contentId)
        return slow_service_container.build_get_content_name_response(
            content_name)

    # @endpoints.method(
    #     # This method takes a ResourceContainer defined above.
    #     ECHO_RESOURCE,
    #     # This method returns an Echo message.
    #     EchoResponse,
    #     path='echo',
    #     http_method='POST',
    #     name='echo')
    # def echo(self, request):
    #     output_content = ' '.join([request.content] * request.n)
    #     return EchoResponse(content=output_content)
    #
    # @endpoints.method(
    #     # This method takes a ResourceContainer defined above.
    #     ECHO_RESOURCE,
    #     # This method returns an Echo message.
    #     EchoResponse,
    #     path='echo/{n}',
    #     http_method='POST',
    #     name='echo_path_parameter')
    # def echo_path_parameter(self, request):
    #     output_content = ' '.join([request.content] * request.n)
    #     return EchoResponse(content=output_content)
    #
    # @endpoints.method(
    #     # This method takes a ResourceContainer defined above.
    #     message_types.VoidMessage,
    #     # This method returns an Echo message.
    #     EchoResponse,
    #     path='echo/getApiKey',
    #     http_method='GET',
    #     name='echo_api_key',
    #     api_key_required=True)
    # def echo_api_key(self, request):
    #     key, key_type = request.get_unrecognized_field_info('key')
    #     return EchoResponse(content=key)
    #
    # @endpoints.method(
    #     # This method takes an empty request body.
    #     message_types.VoidMessage,
    #     # This method returns an Echo message.
    #     EchoResponse,
    #     path='echo/getUserEmail',
    #     http_method='GET',
    #     # Require auth tokens to have the following scopes to access this API.
    #     scopes=[endpoints.EMAIL_SCOPE],
    #     # OAuth2 audiences allowed in incoming tokens.
    #     audiences=['your-oauth-client-id.com'])
    # def get_user_email(self, request):
    #     user = endpoints.get_current_user()
    #     # If there's no user defined, the request was unauthenticated, so we
    #     # raise 401 Unauthorized.
    #     if not user:
    #         raise endpoints.UnauthorizedException
    #     return EchoResponse(content=user.email())


api = endpoints.api_server([ServicesApi])
