from wsgiref.simple_server import make_server
from pyramid.config import Configurator
from pyramid.response import Response
from apscheduler.schedulers.background import BackgroundScheduler
from common.utils.singleton import Singleton


def hello_world(request):
    return Response('Hello World!')


def process_abnormal():
    with Configurator() as config:
        config.add_route('hello', '/hello_world')
        config.add_view(hello_world, route_name='hello')
        app = config.make_wsgi_app()
    server = make_server('0.0.0.0', 8081, app)
    server.serve_forever()


@Singleton
class PyHttpServer:
    def __init__(self):
        self.scheduler = BackgroundScheduler(timezone="Asia/Shanghai")
        self.scheduler.add_job(process_abnormal)

    def start(self):
        self.scheduler.start()
