import endpoints

from endpoints import message_types
from endpoints import messages


class GetContentNameRequest(messages.Message):
    content = messages.StringField(1)


class GetContentNameResponse(messages.Message):
    content = messages.StringField(1)


def get_content_name_request_type():
    return endpoints.ResourceContainer(
        message_types.VoidMessage, contentId=messages.StringField(1))


def get_content_name_response_type():
    return GetContentNameResponse


def build_get_content_name_response(content_name):
    return GetContentNameResponse(content=content_name)
