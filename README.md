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
    # Manipulate kubernetes state
    # ... object = { "kind" : "Pod", "apiVersion" : "v1", ... }
    ctx.kubernetes.create_or_update(object)

    # Export metrics
    # ... metric = { "name" : "power", "group": "my_hook", "set" : 9000, ... }
    ctx.metrics.collect(metric)

    # Use module values for helm chart
    ctx.values.myModule.deployment.replicas = 5


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

    assert out.metrics.data == expected_metrics
    assert out.kube_operations.data == expected_kube_operations
    assert out.values_patches.data == expected_values_patches

    assert out.values.myModule.deployment.repicas == 5
```
