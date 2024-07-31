# MagicPickle

## Example use
```python
from magicpickle import MagicPickle
with MagicPickle(is_local_func=lambda: args.is_local) as mp:
    if mp.is_remote:
        mp.save("hello")
    else:
        print(mp.load())
```
