import functools
import time
import subprocess


def timeit(func):
    """Basic timing decorator"""
    @functools.wraps(func)
    def timed(*args, **kw):
        ts = time.time()
        result = func(*args, **kw)
        te = time.time()
        print(f'{func.__name__}: {(te - ts) * 1000:.2f} ms')
        return result
    return timed


def retry_if_return_is_none(times=1, sleep_secs=1):
    """Decorator - retry a configurable number of times if the return value is None"""
    def wrapper(func):
        @functools.wraps(func)
        def wrapped(*args, **kw):
            count = times
            while count > 0:
                result = func(*args, **kw)
                if result is not None:
                    return result
                else:
                    time.sleep(sleep_secs)
                    count -= 1
                    continue
        return wrapped
    return wrapper


def run_cmd(cmd):
    """Return the first output line from a cmd launched on a shell"""
    pipe = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    output = pipe.communicate()[0]
    return output.decode().split('\n')[0]
