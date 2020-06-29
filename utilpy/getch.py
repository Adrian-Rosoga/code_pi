
"""
Non-blocking
"""

def getch_non_blocking(timeout=1e6):

    from pynput import keyboard
    with keyboard.Events() as events:
        try:
            event = events.get(timeout)
            if hasattr(event.key, 'char'):
                return event.key.char
        except:
            pass
        return None


"""
Blocking
Recipe: http://code.activestate.com/recipes/134892-getch-like-unbuffered-character-reading-from-stdin/
"""


class _Getch:
    """Gets a single character from standard input.  Does not echo to the
    screen."""
    def __init__(self):
        try:
            self.impl = _GetchWindows()
        except ImportError:
            self.impl = _GetchUnix()

    def __call__(self):
        return self.impl()


class _GetchUnix:
    def __init__(self):
        import tty
        import sys

    def __call__(self):
        import sys
        import tty
        import termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


class _GetchWindows:
    def __init__(self):
        import msvcrt

    def __call__(self):
        import msvcrt
        return msvcrt.getch()


getch = _Getch()
