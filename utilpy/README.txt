- Show that ILock is broken

from ilock import ILock

def get_temperature_humidity_RACE_CONDITION():
    try:
        with ILock('HTU21D'):
            obj = HTU21D()
            return obj.read_temperature(), obj.read_humidity()
    except Exception:
        logging.info('Caught exception: %s', sys.exc_info()[0])
        traceback.print_exc()
        return None, None
