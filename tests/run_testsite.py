#pylint: skip-file
import atexit
import os
import psutil
import threading
import time


def start():
    os.system('./manage.py runserver 8111 --noreload')


def kill_django():
    print('Shutting down test API...')
    for p in psutil.process_iter():
        try:
            cmd = p.cmdline
            if './manage.py' in cmd and 'runserver' in cmd and '8111' in cmd:
                p.terminate()
        except:
            pass
    remove_db()


def remove_db():
    try:
        os.remove(os.path.join('/dev', 'shm', 'db.sqlite3'))
    except OSError:
        pass


def run():
    print('Setting up test API...')
    atexit.register(kill_django)
    os.chdir('tests/testsite')
    remove_db()
    t = threading.Thread(target=start)
    t.daemon = True
    t.start()
    time.sleep(2)

run()
