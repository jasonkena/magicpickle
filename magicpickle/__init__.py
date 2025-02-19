import importlib.metadata
from .magicpickle import MagicPickle, send, receive

__version__ = importlib.metadata.version("magicpickle")
