# Deckhouse module SDK

Deckhouse module SDK simplifies writing module hooks for operators:

- [Deckhouse](https://github.com/deckhouse/deckhouse)
- [Addon Operator](https://github.com/flant/addon-operator)
- [Shell Operator](https://github.com/flant/shell-operator) (values are unaccessable)

**NOTE**:
- The API is in alpha stage


## Install

```bash
pip install deckhouse-sdk
```

## Sample hook

```python
# hello.py
from deckhouse_sdk import hook

def main(ctx: hook.Context):
    # Manipulate kubernetes state
    # ... object = { "kind" : "Pod", "apiVersion" : "v1", ... }
    ctx.kubernetes.create_or_update(object)

    # Export metrics
    # ... metric = { "name" : "power", "group": "my_hook", "set" : 9000, ... }
    ctx.metrics.collect(metric)

    # Use in-memory values for helm chart. Shell Operator does not support values, but Addon Operator and Deckhouse do.
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
from deckhouse_sdk import hook

# Inputs
#   initial_values = { ... }
#   binding_context = [ { ... } ]
# Outputs
#   expected_metrics = [ ... ]
#   expected_kube_operations = [ ... ]
#   expected_values_patches = [ ... ]
#   expected_values = { ... }

def test_hello():
    out = hook.testrun(main, binding_context, initial_values)

    assert out.metrics.data == expected_metrics
    assert out.kube_operations.data == expected_kube_operations
    assert out.values_patches.data == expected_values_patches

    assert out.values.myModule.deployment.repicas == 5
```
