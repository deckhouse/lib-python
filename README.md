# Shell Operator Python Framework

This is a framework for [shell-operator](https://github.com/flant/shell-operator) for writing hooks
im Python.

## Install

```bash
pip install shell-operator
```

## Sample hook

```python
# hello.py
import shell_operator as operator

def handle(context: operator.HookContext):
    print("Hello from Python!")

if __name__ == "__main__":
    operator.run(handle, configpath="hello.yaml") # 'config' arg is also supported for raw string
```

```yaml
# hello.yaml
configVersion: v1
onStartup: 10
```

## How to test

```python
# hello_test.py

import shell_operator as operator
from hello import handle

binding_context = [
    {
        # expected binding context
    }
]

expected_metrics = []
expected_kubernetes_operations = []

def test_node_metrics():
    metrics = operator.MetricsExporter(operator.MemStorage())
    kubernetes = operator.KubernetesModifier(operator.MemStorage())
    for ctx in binding_context:
        hook_ctx = operator.HookContext(ctx, metrics=metrics, kubernetes=kubernetes)
        handle(hook_ctx)

    assert metrics.storage.data == expected_metrics
    assert kubernetes.storage.data == expected_kubernetes_operations
```
