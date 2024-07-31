import os
import argparse
import shutil
import socket
import joblib
import tempfile
import subprocess


def default_is_local_func():
    return "think-jason" in socket.gethostname()


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

    def __init__(self, is_local_func=default_is_local_func):
        self.is_local = is_local_func()
        self.is_remote = not self.is_local
        print(f"MagicPickle is_local: {self.is_local}")

        assert shutil.which("wormhole"), "Please install magic-wormhole"

    def __enter__(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.store_path = os.path.join(self.tmpdir.name, "store")
        print(f"MagicPickle tmpdir: {self.tmpdir.name}")

        if self.is_local:
            command = input("Enter wormhole command: ").strip()
            # of the form wormhole receive 89-ohio-buzzard
            assert (
                command.startswith("wormhole receive") and len(command.split()) == 3
            ), "Invalid command received"
            code = command.split()[-1]
            command = f"wormhole receive --accept-file {code}"
            subprocess.run(
                command.split(), cwd=self.tmpdir.name, check=True
            )  # , shell=True)

            assert os.path.exists(
                self.store_path
            ), f"store not found in {self.tmpdir.name}"
            self.store = joblib.load(self.store_path)
        else:
            self.store = []

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if not self.is_local:
            joblib.dump(self.store, self.store_path)
            command = f"wormhole send {self.store_path}"
            subprocess.run(command.split(), check=True)
        self.tmpdir.cleanup()

    def load(self):
        assert self.is_local, "Cannot load in remote mode"
        return self.store.pop(0)

    def save(self, obj):
        assert not self.is_local, "Cannot save in local mode"
        self.store.append(obj)


if __name__ == "__main__":
    # example usage
    parser = argparse.ArgumentParser()
    parser.add_argument("--is_local", action="store_true")
    args = parser.parse_args()

    with MagicPickle(is_local_func=lambda: args.is_local) as mp:
        if mp.is_remote:
            mp.save("hello")
        else:
            print(mp.load())
