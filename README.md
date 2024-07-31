# MagicPickle
`magicpickle` allows you to transfer pickled representations of objects between local and remote instances of scripts, providing a near-seamless way to write code which both accesses data stored remotely and visualizes it locally. This avoids the need to:
- store, load, and sync intermediate data representations between local and remote machines
- use X11 forwarding/VNC with noticable latency

Internally, `magicpickle` uses `joblib` to pickle and unpickle objects, and `magic-wormhole` to transfer the pickled data between local and remote instances of a script.

Note that `magicpickle` assumes that each `mp.save` is associated with a _single_ `mp.load` in the same script; it assumes that both local and remote instances have the same control flow.

## Installation
```pip install magicpickle```

## Usage
Check the docstrings in `src/magicpickle.py` for more information. Example use:

```python
from magicpickle import MagicPickle

with MagicPickle(MY_LOCAL_HOSTNAME) as mp: # or MagicPickle(func_that_returns_true_if_local)
    if mp.is_remote: # or mp.is_local
        mp.save("hello")
    else:
        print(mp.load())
```

## Tmux
`tmux_magicpickle.py` is a script that scrapes your panes and automatically enters the `magic-wormhole` code for you. Add the following to your `~/.tmux.conf` to use it:
```
bind-key g run-shell "python3 PATH_TO/tmux_magicpickle.py"
```
to add the `prefix + g` binding.
