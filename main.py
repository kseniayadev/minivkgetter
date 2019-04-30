import argparse
import os
import uuid

from aiohttp import web

import routes


def factory(low_level_config={}):
    app = web.Application()
    app['HOME'] = os.environ['HOME']
    app['uuid'] = uuid.uuid4().hex
    app['password'] = low_level_config.get('password', '')
    app['local'] = low_level_config.get('local', False)
    app['test_mode'] = False
    app['token'] = None
    app['watcher'] = {}
    app['tasks'] = []
    routes.setup(app)
    return app


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--password', type=str, default='')
    parser.add_argument('--local', default=False, action='store_true')
    parser.add_argument('--port', type=int, default=8080)
    args = parser.parse_args()
    app = factory({
        'password': args.password,
        'local': args.local
    })
    web.run_app(app, port=args.port)
