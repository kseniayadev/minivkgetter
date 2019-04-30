import os
import sys
import time

import aiohttp
import aiofiles


async def get_online(app, uids):
    if app['token'] is None:
        raise RuntimeError('Token not specified')
    url = r'https://api.vk.com/method/users.get'
    if isinstance(uids, int):
        uids = [uids]
    params = {
        'v': '5.95',
        'access_token': app['token'],
        'user_ids': ','.join(map(str, uids)),
        'fields': 'online,last_seen'
    }
    if app['test_mode']:
        params['test_mode'] = 1
    answer = None
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            answer = await resp.json()
    if 'error' in answer:
        err = answer['error']
        return {
            'code': err['error_code'],
            'reason': err['error_msg']
        }
    answer = answer['response']
    for i, val in enumerate(answer):
        answer[i] = {
            'online': val['online'],
            'last_seen': val['last_seen']['time']
        }
    return {
        'code': 0,
        'data': answer
    }


async def watch(app, uid, fields, event):
    files = {}
    base = app['HOME'] + '/.vkgetter/{}/'.format(uid)
    if not os.path.exists(base):
        os.mkdir(base)
        open(base + 'error', 'w').close()
    files['error'] = await aiofiles.open(base + 'error', 'a')
    for field in fields:
        if not os.path.exists(base + field):
            open(base + field, 'w').close()
        files[field] = await aiofiles.open(base + field, mode='a')
    running = True
    try:
        while running:
            await event.wait()
            for field in fields:
                func = getattr(sys.modules[__name__], 'get_' + field)
                if func is None:
                    running = False
                    await files['error'].write(
                        field, 'dont exists\n'
                    )
                    break
                res = await func(app, uid)
                if res['code'] != 0:
                    running = False
                    await files['error'].write(
                        'get', field,
                        'failed with code', res['code'], '\n'
                    )
                    break
                else:
                    res = res['data'][0]
                    line = [str(time.time())]
                    for key in sorted(res.keys()):
                        line.append(res[key])
                    await files[field].write(','.join(map(str, line)) + '\n')
            event.clear()
    finally:
        for file in files.values():
            await file.close()
