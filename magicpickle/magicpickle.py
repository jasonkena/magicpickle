import os
import shutil
import socket
import joblib
import tempfile
import subprocess

from typing import Union, Callable, Optional


class MagicPickle:
    """
    Context manager to save and load objects using magic-wormhole,
    to prevent having to sync np.save/load files or to ssh -X over slow connections
    particularly useful for visualization

    remote: runs computations and saves objects
    local: loads objects and visualizes

    NOTE: assumes that save and load calls are one-to-one
    local and remote must have exact same control flow
    """

    def __init__(
        self,
        local_hostname_or_func: Union[str, Callable[[], bool]],
        verbose: bool = True,
        compress: Union[bool, int] = True,
        local_store_cache: Optional[str] = os.path.join(
            tempfile.gettempdir(), "magicpickle_cache"
        ),
    ):
        """
        Parameters
        ----------
        local_hostname_or_func
            either the hostname of the local machine or a function that returns True if local
        verbose
        compress
            compression level for joblib.dump
        local_store_cache
            persistent cache file used, triggered when empty string passed into prompt on local
        """
        if callable(local_hostname_or_func):
            self.is_local = local_hostname_or_func()
        else:
            self.is_local = local_hostname_or_func in socket.gethostname()
        self.is_remote = not self.is_local

        self.verbose = verbose
        self.compress = compress
        self.local_store_cache = local_store_cache

        if self.verbose:
            print(f"MagicPickle is_local: {self.is_local}")

        assert shutil.which("wormhole"), "Please install magic-wormhole"

    def __enter__(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.store_path = os.path.join(self.tmpdir.name, "store")
        if self.verbose:
            print(f"MagicPickle tmpdir: {self.tmpdir.name}")

        if self.is_local:
            print("Press enter to load from cache")
            command = input("Enter wormhole command: ").strip()
            if command == "":
                # try to load from cache
                assert self.local_store_cache is not None, "local_store_cache is None"
                assert os.path.exists(
                    self.local_store_cache
                ), f"cache not found in {self.local_store_cache}"

                self.store = joblib.load(self.local_store_cache)
            else:
                # of the form wormhole receive 89-ohio-buzzard
                assert (
                    command.startswith("wormhole receive") and len(command.split()) == 3
                ), "Invalid command received"
                code = command.split()[-1]
                command = f"wormhole receive --accept-file {code}"
                subprocess.run(command.split(), cwd=self.tmpdir.name, check=True)

                assert os.path.exists(
                    self.store_path
                ), f"store not found in {self.tmpdir.name}"

                if self.local_store_cache is not None:
                    shutil.copy(self.store_path, self.local_store_cache)

                self.store = joblib.load(self.store_path)
        else:
            self.store = []

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # only run when no errors
        if exc_type is None and self.is_remote:
            joblib.dump(self.store, self.store_path, compress=self.compress)
            command = f"wormhole send {self.store_path}"
            subprocess.run(command.split(), check=True)
        if self.verbose:
            print(f"MagicPickle cleaning tmpdir: {self.tmpdir.name}")
        self.tmpdir.cleanup()

    def load(self):
        assert self.is_local, "Cannot load in remote mode"
        return self.store.pop(0)

    def save(self, obj):
        assert self.is_remote, "Cannot save in local mode"
        self.store.append(obj)


def send(obj, *args, **kwargs):
    """
    Wrapper around MagicPickle to simply send objects
    """
    with MagicPickle(lambda: False, *args, **kwargs) as mp:
        mp.save(obj)


def receive(*args, **kwargs):
    """
    Wrapper around MagicPickle to simply receive objects
    """
    with MagicPickle(lambda: True, *args, **kwargs) as mp:
        return mp.load()
