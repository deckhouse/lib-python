from deckhouse_sdk import hook


def setup():
    def main(_):
        pass

    outputs = hook.testrun(main)
    return outputs


def test_noop_brings_no_kube_operations():
    outputs = setup()
    assert not outputs.kube_operations.data


def test_noop_brings_no_metrics():
    outputs = setup()
    assert not outputs.metrics.data


def test_noop_brings_no_values_changes():
    outputs = setup()

    assert not outputs.values
    assert not outputs.values_patches.initial_values

    assert outputs.values == outputs.values_patches.initial_values
    assert not outputs.values_patches.data
