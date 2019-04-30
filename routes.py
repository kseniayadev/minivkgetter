from aiohttp import web

import logic.routes


async def index(req):
    return web.json_response({
        'code': 0,
        'uuid': req.app['uuid']
    })


async def shutdown(req):
    data = await req.json()
    passwd = data.get('password', '')
    if passwd == req.app['password']:
        raise KeyboardInterrupt
    else:
        return web.json_response({
            'code': 1,
            'reason': 'wrong password'
        })


def setup(app):
    app.router.add_get('/', index, name='index')
    app.router.add_post('/shutdown', shutdown, name='shutdown')
    logic.routes.setup(app)
