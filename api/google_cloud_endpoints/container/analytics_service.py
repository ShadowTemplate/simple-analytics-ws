import endpoints

from endpoints import messages


class UserInfo(messages.Message):
    """"User information of request object for addEvent API method"""

    ip = messages.StringField(1)
    user_agent = messages.StringField(2)
    location = messages.StringField(3)


class AddEventRequest(messages.Message):
    """"Request object for addEvent API method"""

    content_id = messages.StringField(1)
    time = messages.FloatField(2)
    user_info = messages.MessageField(UserInfo.__name__, 3)


class AddEventResponse(messages.Message):
    """"Response object for addEvent API method"""

    content = messages.BooleanField(1)


def add_event_request_type():
    """"Return the request object for addEvent API method"""

    return endpoints.ResourceContainer(
        AddEventRequest, customerId=messages.StringField(1))


def add_event_response_type():
    """"Return the response object for addEvent API method"""

    return AddEventResponse


def build_add_event_response(response):
    """"Build a response for addEvent API method"""

    return AddEventResponse(content=response)
