from shell_operator import hook


def _run_noop():
    def main(_):
        pass

    outputs = hook.testrun(main)
    return outputs


def test_noop_brings_no_kube_operations():
    outputs = _run_noop()
    assert not outputs.kube_operations.data


def test_noop_brings_no_metrics():
    outputs = _run_noop()
    assert not outputs.metrics.data


def test_noop_brings_no_values_changes():
    outputs = _run_noop()

    assert not outputs.values
    assert not outputs.values_patches.initial_values

    assert outputs.values == outputs.values_patches.initial_values
    assert not outputs.values_patches.data
