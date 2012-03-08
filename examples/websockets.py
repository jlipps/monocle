import sys
import new
import simplejson

import monocle
from monocle import _o, Return
monocle.init('tornado') # Only works with Tornado right now

from monocle.stack import eventloop
from monocle.stack.network import add_service, Service
from monocle.stack.network.http import HttpHeaders, WebSocketServer

SOCKET_HTML = """
<!doctype html>
<html>
  <head>
    <meta charset="UTF-8">
    <title>WebSocket Echo</title>
    <script src="http://ajax.googleapis.com/ajax/libs/jquery/1.7.1/jquery.min.js"></script>
  </head>
  <body>
    <h1>WebSocket Reverse Echo</h1>
    <section>Your message backwards: <span id="content"></span></section>
    <input id="message" type="text" style="margin: 20px 0px;"/>
    <section>(You typed: <span id="realContent"></span>)</section>

    <script>
        var ws = new WebSocket('ws://localhost:8088/ws/');
        ws.onopen = function(event) { console.log("Opened socket conn"); };
        ws.onclose = function(event) { console.log("Closed socket conn"); };
        ws.onmessage = function(event) {
            var str = event.data.toString();
            var reversed = str.split("").reverse().join("");
            $('#content').prepend(reversed);
            $('#realContent').append(str);
        };
        $('#message').keyup(function() {
            ws.send($(this).val());
            $(this).val('');
        });
    </script>
  </body>
</html>
"""

@_o
def web_handler():
    yield Return(SOCKET_HTML)

@_o
def websocket_handler(message):
    yield Return(message)


add_service(WebSocketServer(web_handler, websocket_handler, 8088))
eventloop.run()
