import asyncio

from aiohttp import web

import logic


async def set_token(req):
    data = await req.json()
    passwd = data.get('password')
    if passwd != req.app['password']:
        return web.json_response({
            'code': 1,
            'reason': 'wrong password'
        })
    token = data.get('token')
    if token is None:
        return web.json_response({
            'code': 1,
            'reason': 'token not specified'
        })
    req.app['token'] = token
    return web.json_response({
        'code': 0
    })


async def activate_test_mode(req):
    data = await req.json()
    passwd = data.get('password')
    if passwd != req.app['password']:
        return web.json_response({
            'code': 1,
            'reason': 'wrong password'
        })
    req.app['test_mode'] = True
    return web.json_response({
        'code': 0
    })


async def getinfo(req):
    data = await req.json()
    passwd = data.get('password')
    if passwd != req.app['password']:
        return web.json_response({
            'code': 1,
            'reason': 'wrong password'
        })
    uid = data.get('uid')
    if uid is None:
        return web.json_response({
            'code': 1,
            'reason': 'user id not specified'
        })
    if not isinstance(uid, (int, list)):
        return web.json_response({
            'code': 1,
            'reason': 'wrong uid'
        })
    method = data.get('method', 'basic')
    if not hasattr(logic, 'get_' + method):
        return web.json_response({
            'code': 1,
            'reason': 'invalid method'
        })
    try:
        res = await getattr(logic, 'get_' + method)(req.app, uid)
    except RuntimeError:
        return web.json_response({
            'code': 1,
            'reason': 'token not specified'
        })
    return web.json_response(res)


async def setwatch(req):
    data = await req.json()
    passwd = data.get('password')
    if passwd != req.app['password']:
        return web.json_response({
            'code': 1,
            'reason': 'wrong password'
        })
    uid = data.get('uid')
    if not isinstance(uid, int):
        return web.json_response({
            'code': 1,
            'reason': 'invalid uid'
        })
    fields = data.get('methods')
    if isinstance(fields, str):
        fields = [fields]
    if not isinstance(fields, list):
        return web.json_response({
            'code': 1,
            'reason': 'invalid fields'
        })
    app = req.app
    event = asyncio.Event()
    app['watcher'][uid] = event
    tsk = asyncio.create_task(logic.watch(app, uid, fields, event))
    app['tasks'].append(tsk)
    return web.json_response({
        'code': 0
    })


async def update(req):
    data = await req.json()
    passwd = data.get('password')
    if passwd != req.app['password']:
        return web.json_response({
            'code': 1,
            'reason': 'wrong password'
        })
    for event in req.app['watcher'].values():
        event.set()
    return web.json_response({
        'code': 0
    })


def setup(app):
    app.router.add_post('/activateTestMode', activate_test_mode)
    app.router.add_post('/setToken', set_token)
    app.router.add_post('/api', getinfo)
    app.router.add_post('/watch', setwatch)
    app.router.add_post('/update', update)
