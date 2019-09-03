import sys
import itertools

try:
    import StringIO
    import cStringIO
except ImportError:
    pass

from io import BytesIO

running_python_3 = sys.version_info[0] == 3


def range_fn(start=0, stop=None):
    if running_python_3:
        return range(start, stop)
    else:
        return iter(itertools.count(start).next, stop)
