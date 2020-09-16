#coding: utf-8

import logging
import json

from django.utils.deprecation import MiddlewareMixin


apiLogger = logging.getLogger('api')

class ApiLoggingMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == 'GET':
            body = dict(request.GET)
        else:
            try:
                body = json.loads(request.body)
            except ValueError:
                body = {}
            except Exception as e:
                apiLogger.exception(e)
                body = {}
            body.update(dict(request.POST))

        response = self.get_response(request)

        if response.status_code != 200:
            apiLogger.error("{} {} {} {} {} {}".format(
                request.user, request.method, response.status_code,
                request.path, body,  response.content
            ))
        else:
            if request.method == 'GET':
                apiLogger.info("{} {} {} {} {}".format(
                    request.user, request.method, response.status_code,
                    request.path, body
                ))
            else:
                apiLogger.info("{} {} {} {} {} {}".format(
                    request.user, request.method, response.status_code,
                    request.path, body,  response.content
                ))

        return response
