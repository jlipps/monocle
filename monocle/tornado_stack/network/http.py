# -*- coding: utf-8 -*-
#
# by Steven Hazel

import urlparse

import tornado.httpclient
import tornado.httpserver
import tornado.web
import tornado.websocket

from monocle import _o, Return, VERSION, launch
from monocle.callback import Callback
from monocle.stack.network import Client
from monocle.stack.network.http import HttpHeaders, HttpClient

class HttpException(Exception): pass

class HttpClient(HttpClient):
    @classmethod
    @_o
    def query(self, url, headers=None, method='GET', body=None):
        _http_client = tornado.httpclient.AsyncHTTPClient()
        req = tornado.httpclient.HTTPRequest(url,
                                             method=method,
                                             headers=headers or {},
                                             body=body)
        cb = Callback()
        _http_client.fetch(req, cb)
        response = yield cb
        yield Return(response)

class HttpServer(object):
    def __init__(self, handler, port):
        self.handler = handler
        self.port = port

    def _add(self, el):
        @_o
        def _handler(request):
            try:
                code, headers, content = yield launch(self.handler, request)
            except:
                code, headers, content = 500, {}, "500 Internal Server Error"
            request.write("HTTP/1.1 %s\r\n" % code)
            headers.setdefault('Server', 'monocle/%s' % VERSION)
            headers.setdefault('Content-Length', str(len(content)))
            for name, value in headers.iteritems():
                request.write("%s: %s\r\n" % (name, value))
            request.write("\r\n")
            request.write(content)
            request.finish()
        self._http_server = tornado.httpserver.HTTPServer(
            _handler,
            io_loop=el._tornado_ioloop)
        self._http_server.listen(self.port)

class WebSocketServer(HttpServer):
    def __init__(self, web_handler, ws_handler, port):
        self.web_handler = web_handler
        self.ws_handler = ws_handler
        self.port = port

    def _add(self, el):
        web_handler = self.web_handler
        @_o
        def _get(self):
            content = yield launch(web_handler)
            self.write(content)
        WebHandler = type('WebHandler', (
            tornado.web.RequestHandler,),
            {'get': _get})

        ws_handler = self.ws_handler
        @_o
        def _on_message(self, message):
            response = yield launch(ws_handler, message)
            self.write_message(response)
        WSHandler = type('WSHandler',
            (tornado.websocket.WebSocketHandler,),
            {'on_message': _on_message})

        self._tornado_app = tornado.web.Application([
            (r'^/', WebHandler),
            (r'^/ws/', WSHandler)])
        self._http_server = tornado.httpserver.HTTPServer(
            self._tornado_app, io_loop=el._tornado_ioloop)
        self._http_server.listen(self.port)


