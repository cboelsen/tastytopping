# pylint: skip-file
import atexit
import os
import psutil
import socket
import subprocess
import threading
import time

COMMAND = 'python manage.py runserver 8111 --noreload'


def start():
    cmd = COMMAND
    verbose = os.environ.get('VERBOSE')
    if not verbose:
        cmd += ' > /dev/null 2>&1'
    os.system(cmd)


def wait_for_django_port_open():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while sock.connect_ex(('127.0.0.1', 8111)) != 0:
        time.sleep(0.05)


def kill_django():
    command = COMMAND.split()
    for p in psutil.process_iter():
        try:
            if p.cmdline() == command:
                p.terminate()
                print('Shut down test API...')
        except:
            pass
    remove_db()


def remove_db():
    try:
        os.remove(os.path.join('/dev', 'shm', 'db.sqlite3'))
    except OSError:
        pass


def setup_tastypie_site():
    atexit.register(kill_django)
    os.chdir(os.path.join('tests', 'testsite'))
    remove_db()
    try:
        subprocess.check_call('python manage.py syncdb --noinput'.split())
    except subprocess.CalledProcessError:
        subprocess.check_call('python manage.py makemigrations testapp --noinput'.split())
        subprocess.check_call('python manage.py migrate --noinput'.split())
    subprocess.check_call('python manage.py createsuperuser --noinput --username=testuser --email=none@test.test'.split())
    t = threading.Thread(target=start)
    t.daemon = True
    t.start()
    wait_for_django_port_open()
