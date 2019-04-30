#! /usr/bin/python3.7
import cmd
import datetime
import os
import json
import subprocess
import sys
import time

import requests

HOME = os.environ['HOME']


class CLI(cmd.Cmd):
    intro = 'Welcome to control panel for VKGetter'
    prompt = '() '

    def __init__(self):
        super(CLI, self).__init__()
        self.host = None
        self.port = None
        self.password = None
        self.run = True
        self.recordfile = None
        if self.localcheck():
            self.localconnect()

    def do_localcreate(self, args):
        '''
        Run a server on localhost
        Warning: your must have all requeirements without venv!
        Usage: create [<port,default=8080>] [local,default=False] [-<password>]
        local -- enable local filter
        '''
        args = args.split()
        port = 8080
        local = False
        password = '--password passwd '
        for arg in args:
            if arg == 'local':
                local = True
            elif arg.isnumeric():
                port = arg
            elif arg[0] == '-':
                password = arg[1:]
                if len(password) > 0:
                    password = '--password ' + password + ' '
                else:
                    password = ''
            else:
                print('Wrong argument format')
                return
        if self.localcheck():
            print('Current server running. Connect to it and shutdown')
        file = os.path.abspath('./main.py')
        command = 'python3.7 {} {}--port {}{}'.format(
            file,
            password,
            port,
            ' --local' if local else ''
        )
        process = subprocess.Popen(command.split(), stdout=subprocess.DEVNULL)
        time.sleep(1)
        if process.poll() is not None:
            print('Error starting a new server')
            return
        path = os.path.abspath('{}/.vkgetter/info'.format(HOME))
        with open(path, 'w') as f:
            payload = {
                'pid': str(process.pid),
                'port': str(port),
                'password': password.split()[-1] if len(password) > 0 else ''
            }
            json.dump(payload, f)
        print('Successfuly created server on localhost:{}'.format(port))
        if self.localconnect() is None:
            if password != '':
                self.password = password.split()[-1]
            else:
                self.password = ''
        else:
            return True

    def do_localcheck(self, args):
        '''Check state of localserver'''
        res = self.localcheck()
        if res is True:
            print('Server runned')
        else:
            print('Server are not running')

    def do_shutdown(self, args):
        '''Shutdown the connected server'''
        if self.host is None:
            print('No connection')
            return
        password = self.password
        url = 'http://{}:{}/shutdown'.format(self.host, self.port)
        res = False
        try:
            res = requests.post(url, json={'password': password})
            print('Failed to shutdown')
            print('Reason:', res.json().get('password'))
        except requests.exceptions.ConnectionError:
            res = True
        if res:
            print('Successfuly shutdown')
            self.host = None
            self.port = None
            self.password = None
            os.remove('{}/.vkgetter/info'.format(HOME))
            self.prompt = '() '
            if self.recordfile is not None:
                self.prompt = 'R' + self.prompt

    def do_settoken(self, args):
        '''
        Set app token
        Usage: settoken <token>
        '''
        args = args.split()
        if len(args) != 1:
            print('Wrong use')
            return
        token = args[0]
        if self.host is None:
            print('No connection')
            return
        url = 'http://{}:{}/setToken'.format(self.host, self.port)
        res = requests.post(url, json={
            'password': self.password,
            'token': token
        })
        res = res.json()
        if res.get('code', 1) != 0:
            print('Error')
            print('Reason:', res.get('reason', 'none'))

    def do_activatetestmode(self, args):
        '''Activate test mode'''
        if len(args) != 0:
            print('Wrong use')
            return
        if self.host is None:
            print('No connection')
            return
        url = 'http://{}:{}/activateTestMode'.format(self.host, self.port)
        res = requests.post(url, json={
            'password': self.password,
        })
        res = res.json()
        if res.get('code', 1) != 0:
            print('Error')
            print('Reason:', res.get('reason', 'none'))

    def do_recordscript(self, args):
        '''
        Record commands to save in script. For stop record type end
        Usage: recordscript <file> [norun]
        norun -- disable exec commands while record
        '''
        args = args.split()
        if len(args) not in (1, 2):
            print('Wrong use')
            return
        run = True
        file = args[0]
        if len(args) == 2:
            if args[1] == 'norun':
                run = False
            else:
                print('Wrong use')
                return
        file += '.vgs'
        self.recordfile = open(file, 'w')
        self.run = run
        if self.recordfile is not None:
            self.prompt = 'R' + self.prompt

    def do_runscript(self, args):
        '''
        Run script from file
        Usage: runscript <file>
        '''
        args = args.split()
        if len(args) != 1:
            print('Wrong use')
            return
        file = args[0] + '.vgs'
        if not os.path.isfile(file):
            print(file, 'is not file')
            return
        self.runscript(file)

    def do_sleep(self, args):
        '''
        Sleep
        Usage: sleep <time>
        time -- time for sleep in seconds
        '''
        arg = args.split()
        if len(arg) != 1:
            print('Wrong use')
            return
        arg = arg[0]
        if not arg.isnumeric():
            print('Wrong use')
            return
        arg = int(arg)
        time.sleep(arg)

    def do_online(self, args):
        '''
        Return online status of user
        Usage: online <uid>
        '''
        args = args.split()
        if len(args) != 1:
            print('Wrong use')
            return
        arg = args[0]
        if not arg.isnumeric():
            print('Wrong argument')
            return
        arg = int(arg)
        if self.host is None:
            print('No connection')
            return
        url = 'http://{}:{}/api'.format(self.host, self.port)
        res = requests.post(url, json={
            'password': self.password,
            'uid': arg,
            'method': 'online'
        }).json()
        if res.get('code', 1) != 0:
            print('Error')
            print('Reason:', res.get('reason', 'none'))
            return
        res = res['data'][0]
        print('Online:', 'yes' if res['online'] == 1 else 'no')
        if res['online'] == 0:
            last = datetime.datetime.utcfromtimestamp(res['last_seen'])
            last = last.strftime('%Y-%m-%d %H:%M:%S UTC+0')
            print('Last seen:', last)

    def do_update(self, args):
        '''Update data on server'''
        if len(args) != 0:
            print('Wrong use')
            return
        if self.host is None:
            print('No connection')
            return
        url = 'http://{}:{}/update'.format(self.host, self.port)
        res = requests.post(url, json={
            'password': self.password,
        }).json()
        if res.get('code', 1) != 0:
            print('Error')
            print('Reason:', res.get('reason', 'none'))
            return

    def do_watch(self, args):
        '''
        Set uid on watching
        Usage: watch <uid> <field1> [<field2> ...]
        '''
        args = args.split()
        if len(args) <= 1:
            print('Wrong use')
            return
        arg = args[0]
        arg = int(arg)
        if self.host is None:
            print('No connection')
            return
        url = 'http://{}:{}/watch'.format(self.host, self.port)
        res = requests.post(url, json={
            'password': self.password,
            'uid': arg,
            'methods': args[1:]
        }).json()
        if res.get('code', 1) != 0:
            print('Error')
            print('Reason:', res.get('reason', 'none'))
            return

    def do_quit(self, args):
        '''Quit from CLI'''
        return True

    def localcheck(self):
        path = os.path.abspath('{}/.vkgetter/info'.format(HOME))
        if os.path.isfile(path):
            return True
        return False

    def localconnect(self):
        path = os.path.abspath('{}/.vkgetter/info'.format(HOME))
        with open(path) as f:
            try:
                info = json.load(f)
            except json.JSONDecodeError:
                print('Wrong format file ~/.vkgetter')
                return True
        pid = info.get('pid', 'error')
        if not pid.isnumeric():
            print('Wrong format file ~/.vkgetter')
            return True
        pid = int(pid)
        port = info.get('port', 'error')
        if not port.isnumeric():
            print('Wrong format file ~/.vkgetter')
            return True
        self.password = info.get('password')
        return self.connect('localhost', port)

    def connect(self, host, port):
        res = requests.get('http://{}:{}/'.format(host, port))
        if res.status_code != 200:
            print('Wrong server')
            return True
        try:
            res = json.loads(res.text)
        except json.JSONDecodeError:
            print('Wrong server')
            return True
        uuid = res.get('uuid')
        if uuid is None:
            print('Wrong server')
            return True
        code = str(res.get('code', 'error'))
        if not code.isnumeric():
            print('Wrong server')
            return True
        if int(code) != 0:
            print('Server return code {}'.format(code))
            return True
        self.host = host
        self.port = port
        self.prompt = '({}:{}) '.format(host, port)
        if self.recordfile is not None:
            self.prompt = 'R' + self.prompt

    def runscript(self, file):
        file = open(file)
        self.cmdqueue.extend(file.readlines())
        file.close()

    def precmd(self, line):
        if self.recordfile is not None:
            if line == 'end':
                self.recordfile.close()
                self.recordfile = None
                self.run = True
                self.prompt = self.prompt[1:]
                return ''
            if line.startswith('recordscript'):
                return ''
            self.recordfile.write(line)
            self.recordfile.write('\n')
        if self.run:
            return line
        return ''

    def emptyline(self):
        pass


if __name__ == '__main__':
    if not os.path.exists('{}/.vkgetter'.format(HOME)):
        os.mkdir('{}/.vkgetter'.format(HOME))
    elif os.path.isfile('{}/.vkgetter'.format(HOME)):
        print('~/.vkgetter is file')
        sys.exit(1)
    argv = sys.argv[1:]
    cli = CLI()
    if len(argv) > 0:
        for arg in argv:
            cli.do_runscript(arg)
    cli.cmdloop()
