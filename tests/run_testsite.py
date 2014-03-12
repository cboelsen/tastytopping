#pylint: skip-file
import atexit
import os
import psutil
import threading
import time

COMMAND = 'python manage.py runserver 8111 --noreload'


def start():
    os.system(COMMAND)


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


def run():
    print('Setting up test API...')
    atexit.register(kill_django)
    os.chdir(os.path.join('tests', 'testsite'))
    remove_db()
    os.system('python manage.py syncdb --noinput')
    os.system('python manage.py createsuperuser --noinput --username=testuser --email=none@test.test')
    t = threading.Thread(target=start)
    t.daemon = True
    t.start()
    os.system('python manage.py user')

run()
