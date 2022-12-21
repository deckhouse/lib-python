# Shell Operator Python Framework

This is a framework for [shell-operator](https://github.com/flant/shell-operator) for writing hooks
im Python.

## Sample hook

```python
# hello.py
import shell_operator as operator

def main(context: operator.HookContext):
    print("Hello from Python!")

if __name__ == "__main__":
    operator.run(main, "hello.yaml")
```

```yaml
# hello.yaml
configVersion: v1
onStartup: 10
```
