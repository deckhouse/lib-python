# Shell Operator Python Framework

Simplifies writing [shell-operator](https://github.com/flant/shell-operator) hooks in Python.

## Install

```bash
pip install shell-operator
```

## Sample hook

```python
# hello.py
from shell_operator import hook

def main(ctx: hook.Context):
    # ... object = { "kind" : "Pod", "apiVersion" : "v1", ... }
    ctx.output.kubernetes.create_or_update(object)
    # ... metric = { "name" : "power", "group": "my_hook", "set" : 9000, ... }
    ctx.output.metrics.collect(metric)


if __name__ == "__main__":
    hook.run(main, configpath="hello.yaml") # 'config' arg is also supported for raw string
```

```yaml
# hello.yaml
configVersion: v1
onStartup: 10
```

## How to test

An example for pytest

```python
# hello_test.py

from hello import main
from shell_operator import hook

# binding_context = [ { ... } ]
# expected_metrics = [ ... ]
# expected_kube_operations = [ ... ]

def test_hello():
    out = hook.testrun(main, binding_context)

    assert out.metrics.storage.data == expected_metrics
    assert out.kubernetes.storage.data == expected_kube_operations
```
