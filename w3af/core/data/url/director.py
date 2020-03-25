import http.client
import socket

from urllib.request import OpenerDirector, ProxyHandler, UnknownHandler, HTTPHandler, HTTPDefaultErrorHandler, \
    HTTPRedirectHandler, HTTPErrorProcessor, HTTPSHandler, Request


class CustomOpenerDirector(OpenerDirector):
    def open(self, full_url, data=None, timeout=socket._GLOBAL_DEFAULT_TIMEOUT):
        """
        Overriding to remove the timeout kwarg which was being used below to
        override my own HTTPRequest.timeout attribute.
        """
        # accept a URL or a Request object
        if isinstance(full_url, str):
            req = Request(full_url, data)
        else:
            req = full_url
            if data is not None:
                req.add_data(data)

        # This is what I want to remove and the reason to override
        # req.timeout = timeout
        protocol = req.get_type()

        # pre-process request
        meth_name = protocol+"_request"
        for processor in self.process_request.get(protocol, []):
            meth = getattr(processor, meth_name)
            req = meth(req)

        response = self._open(req, data)

        # post-process response
        meth_name = protocol+"_response"
        for processor in self.process_response.get(protocol, []):
            meth = getattr(processor, meth_name)
            response = meth(req, response)

        return response


def build_opener(director_klass, handlers):
    """Create an opener object from a list of handlers.

    The opener will use several default handlers, including support
    for HTTP, FTP and when applicable, HTTPS.

    If any of the handlers passed as arguments are subclasses of the
    default handlers, the default handlers will not be used.
    """
    import types

    def isclass(obj):
        return isinstance(obj, type)

    opener = director_klass()
    default_classes = [ProxyHandler, UnknownHandler, HTTPHandler,
                       HTTPDefaultErrorHandler, HTTPRedirectHandler,
                       HTTPErrorProcessor]
    if hasattr(http.client, 'HTTPS'):
        default_classes.append(HTTPSHandler)
    skip = set()
    for klass in default_classes:
        for check in handlers:
            if isclass(check):
                if issubclass(check, klass):
                    skip.add(klass)
            elif isinstance(check, klass):
                skip.add(klass)
    for klass in skip:
        default_classes.remove(klass)

    for klass in default_classes:
        opener.add_handler(klass())

    for h in handlers:
        if isclass(h):
            h = h()
        opener.add_handler(h)
    return opener
