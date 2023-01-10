from shell_operator import hook


def test_value_change_is_stored():
    def main(ctx):
        ctx.values.a = 42

    initial_values = {"a": 33}
    outputs = hook.testrun(main, initial_values=initial_values)

    assert outputs.values.a == 42
    assert outputs.values_patches.data == [
        {"op": "change", "path": "/a", "value": 42},
    ]


def test_unchanged_value_generates_no_patches():
    def main(ctx):
        ctx.values.a = 42

    initial_values = {"a": 42}
    outputs = hook.testrun(main, initial_values=initial_values)

    assert outputs.values.a == 42
    assert not outputs.values_patches.data


def test_added_value_is_stored():
    def main(ctx):
        ctx.values.b = 42

    initial_values = {"a": 33}
    outputs = hook.testrun(main, initial_values=initial_values)

    assert outputs.values.a == 33
    assert outputs.values.b == 42
    assert outputs.values_patches.data == [
        {"op": "add", "path": "/b", "value": 42},
    ]


def test_removed_value_is_not_stored():
    def main(ctx):
        del ctx.values.a

    initial_values = {"a": 33}
    outputs = hook.testrun(main, initial_values=initial_values)

    assert not outputs.values
    assert outputs.values_patches.data == [
        {"op": "remove", "path": "/a"},
    ]


def test_initial_values_remain_unchanged():
    def main(ctx):
        del ctx.values.a  # remove
        ctx.values.b = 99  # change
        ctx.values.c = 101  # add

    initial_values = {"a": 33, "b": 42}
    outputs = hook.testrun(main, initial_values=initial_values)

    assert outputs.values_patches.initial_values == initial_values


def test_list_values_changes_have_separate_patches():
    def main(ctx):
        ctx.values.a.append(42)
        ctx.values.a.append(101)

    initial_values = {"a": [33]}
    outputs = hook.testrun(main, initial_values=initial_values)

    assert outputs.values_patches.data == [
        {"op": "add", "path": "/a/1", "value": 42},
        {"op": "add", "path": "/a/2", "value": 101},
    ]


def test_values_do_not_support_sets():
    """
    This tests shows the set-list mismatch on Python side in the changes.

    Sets will actually break hooks because they are not JSON-serializable and wriring patches to
    files uses `json.dumps`. User can always do list(set) in values.

    """

    def main(ctx):
        ctx.values.a = set(ctx.values.a)
        ctx.values.a.add(42)
        ctx.values.a.add(101)

    initial_values = {"a": [33]}
    outputs = hook.testrun(main, initial_values=initial_values)

    assert outputs.values_patches.data != [
        {"op": "add", "path": "/a/1", "value": 42},
        {"op": "add", "path": "/a/2", "value": 101},
    ]
