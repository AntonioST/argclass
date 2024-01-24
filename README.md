Use argparse as Dataclass fields
================================

Example
-------

```python
from argclass import arg, AbstractOptions


class CliMain(AbstractOptions):
    a: int = arg('-a')

    def run(self):
        print(self.a)  # 2


if __name__ == '__main__':
    CliMain().main(['-a=2'])
```

