"""Module for errors that the API might encounter"""

class WalmartException(Exception):
    """
    Base Class for Walmart Api Exceptions.
    """


class InvalidParameterException(WalmartException):
    """
    Exception thrown if an invalid parameter is passed to a function
    """
    pass


class InvalidRequestException(WalmartException):
    """
    Exception thrown if an invalid request response is thrown by Walmart
    """

    def __init__(self, status_code, **kwargs):
        error_message = 'Error'
        if status_code == 400:
            error_message = 'Bad Request'
            if 'detail' in kwargs and kwargs['detail']:
                error_message = error_message + ' - ' + str(kwargs['detail'])
        elif status_code == 403:
            error_message = 'Forbidden'
        elif status_code == 404:
            error_message = 'Wrong endpoint'
        elif status_code == 414:
            error_message = 'Request URI too long'
        elif status_code == 500:
            error_message = 'Internal Server Error'
        elif status_code == 502:
            error_message = 'Bad Gateway'
        elif status_code == 503:
            error_message = 'Service Unavailable/ API maintenance'
        elif status_code == 504:
            error_message = 'Gateway Timeout'
        message = '[Request failed] Walmart server answered with the following error: {0:s}. Status code: {1:d}'.format(error_message, status_code)
        super(self.__class__, self).__init__(message)
    pass


class DailyCallLimit(WalmartException):
    """
    Exception for when user goes over the daily limit of API calls
    """
    pass
