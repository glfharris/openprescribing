from BaseHTTPServer import BaseHTTPRequestHandler
from BaseHTTPServer import HTTPServer
import logging
import requests
import socket
from threading import Thread
import urlparse
import os


FIXTURES_BASE = 'frontend/tests/fixtures/functional/'
logger = logging.getLogger(__name__)


def _load_json(name):
    return open("%s/%s.json" % (FIXTURES_BASE, name), 'r').read()


class MockApiRequestHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        logger.info(format % args)

    def do_GET(self):
        o = urlparse.urlparse(self.path)
        q = urlparse.parse_qs(o.query)
        data = {}
        if '/spending_by_ccg' in o.path:
            code = q.get('code')[0]
            if code == '2.12':
                data = _load_json('spending_by_ccg_denom')
            elif code == '0212000AA':
                data = _load_json('spending_by_ccg_num')
        elif '/bnf_code' in o.path:
            code = q.get('q')[0]
            if code.startswith('0212000AA'):
                data = _load_json('bnf_code_num')
            elif code.startswith('2.12'):
                data = _load_json('bnf_code_denom')
        elif '/org_location' in o.path:
            data = _load_json('org_location_ccg')
        elif '/measure_by_ccg/' in o.path:
            data = _load_json('measure_by_ccg')
        elif '/measure/' in o.path:
            data = _load_json('measure')
        if data:
            self.send_response(requests.codes.ok)
        else:
            logger.error("Unhandled path %s" % self.path)
            self.send_response(requests.codes.not_found)
        self.send_header('Content-Type', 'application/json')
        self.send_header('access-control-allow-origin', '*')
        self.end_headers()
        self.wfile.write(data)
        return


class MockApiServer(object):
    def __init__(self, port=None):
        if port is None:
            port = urlparse.urlparse(os.environ['API_HOST']).port
        self.port = port

    def start(self):
        mock_server = HTTPServer(
            ('0.0.0.0', self.port), MockApiRequestHandler)
        self.mock_server_thread = Thread(target=mock_server.serve_forever)
        self.mock_server_thread.setDaemon(True)
        self.mock_server_thread.start()
        logger.info("Started mock API server on port %s" % self.port)

    @classmethod
    def api_port(cls):
        """A port suitable for running the API.
        """
        return 6060
