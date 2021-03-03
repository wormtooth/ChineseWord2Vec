import logging
from functools import wraps
import sys
import traceback


class BaseLogger:

    """Base class for simple logging functionality.

    It can be used as a regular logging.Logger, and it also provides a
    decorator method BaseLogger.catch to catch exceptions of functions and
    log them.

    Attributes:
        datefmt (str): date format of logging
        fmt (str): message format of logging
        level (int): logging level
        logger (logging.Logger): logger
        name (str): name of the logger
    """

    def __init__(self,
                 name='',
                 fmt='[%(asctime)s][%(levelname)s] %(message)s',
                 datefmt='%Y-%m-%d %H:%M:%S',
                 level=logging.DEBUG,
                 **kwargs):

        self.name = name
        self.fmt = fmt
        self.datefmt = datefmt
        self.level = level

        self.logger = logging.getLogger(name=name)
        self.logger.setLevel(level)

    def catch(self, func=None, level=logging.DEBUG, trace=False):
        """A decorator to catch exceptions from functions and log them

        Args:
            func (callable, optional): function to be decorated
            level (int, optional): logging level
            trace (bool, optional): whether or not to log traceback info

        Returns:
            callable: decorated function or decorator
        """
        def _catch(f):

            @wraps(f)
            def wrapped(*args, **kwargs):
                try:
                    return f(*args, **kwargs)
                except Exception as e:
                    name = f.__name__
                    msg = f'{name}: {e}'
                    if trace:
                        tb = ''.join(traceback.format_tb(e.__traceback__))
                        msg = f'{msg} \n {tb}'
                    self.logger.log(level, msg)

            return wrapped

        if func is None:
            return _catch
        return _catch(func)

    @property
    def formatter(self):
        """logging.Formatter
        """
        return logging.Formatter(fmt=self.fmt, datefmt=self.datefmt)

    def log_to_stdout(self):
        """Log messages to stdout.
        """
        for handler in self.logger.handlers:
            if handler.__class__ is logging.StreamHandler:
                return
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(self.level)
        handler.setFormatter(self.formatter)
        self.logger.addHandler(handler)

    def __getattr__(self, key):
        """Redirect missing attributes to self.logger
        """
        return getattr(self.logger, key)


class FileLogger(BaseLogger):

    """Simple class that logs messages to a file.

    Attributes:
        filename (str): path to the log file
    """

    def __init__(self, filename, **kwargs):
        super().__init__(**kwargs)

        for handler in self.logger.handlers:
            if isinstance(handler, logging.FileHandler) and handler.baseFilename == filename:
                return
        self.filename = filename
        fh = logging.FileHandler(filename)
        fh.setLevel(self.level)
        fh.setFormatter(self.formatter)
        self.logger.addHandler(fh)