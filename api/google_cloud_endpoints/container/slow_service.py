import endpoints

from endpoints import message_types
from endpoints import messages


class GetContentNameRequest(messages.Message):
    """"Request object for getContentName API method"""

    content = messages.StringField(1)


class GetContentNameResponse(messages.Message):
    """"Response object for getContentName API method"""

    content = messages.StringField(1)


def get_content_name_request_type():
    """"Return the request object for getContentName API method"""

    return endpoints.ResourceContainer(
        message_types.VoidMessage, contentId=messages.StringField(1))


def get_content_name_response_type():
    """"Return the response object for getContentName API method"""

    return GetContentNameResponse


def build_get_content_name_response(content_name):
    """"Build a response for getContentName API method"""

    return GetContentNameResponse(content=content_name)
