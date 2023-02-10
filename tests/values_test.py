from dotmap import DotMap

from deckhouse import hook


def test_value_change_is_stored():
    def main(ctx):
        ctx.values.a = 42

    initial_values = DotMap({"a": 33})
    outputs = hook.testrun(main, initial_values=initial_values)

    assert outputs.values.a == 42
    assert outputs.values_patches.data == [
        {"op": "add", "path": "/a", "value": 42},
    ]


def test_unchanged_value_generates_no_patches():
    def main(ctx):
        ctx.values.a = 42

    initial_values = DotMap({"a": 42})
    outputs = hook.testrun(main, initial_values=initial_values)

    assert outputs.values.a == 42
    assert not outputs.values_patches.data


def test_added_value_is_stored():
    def main(ctx):
        ctx.values.b = 42

    initial_values = DotMap({"a": 33})
    outputs = hook.testrun(main, initial_values=initial_values)

    assert outputs.values.a == 33
    assert outputs.values.b == 42
    assert outputs.values_patches.data == [
        {"op": "add", "path": "/b", "value": 42},
    ]


def test_removed_value_is_not_stored():
    def main(ctx):
        del ctx.values.a

    initial_values = DotMap({"a": 33})
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

    initial_values = DotMap({"a": 33, "b": 42})
    outputs = hook.testrun(main, initial_values=initial_values)

    assert outputs.values_patches.initial_values == initial_values


def test_list_values_changes_have_separate_patches():
    def main(ctx):
        ctx.values.a.append(42)
        ctx.values.a.append(101)

    initial_values = DotMap({"a": [33]})
    outputs = hook.testrun(main, initial_values=initial_values)

    assert outputs.values_patches.data == [
        {"op": "remove", "path": "/a"},
        {"op": "add", "path": "/a", "value": [33, 42, 101]},
    ]


def test_values_do_not_support_sets():
    """
    This tests shows the set-list mismatch on Python side in the changes.

    Sets will actually break hooks because they are not JSON-serializable, and we write patches to
    uses `json.dumps`. User can always do list(set) in values.

    """

    def main(ctx):
        ctx.values.a = set(ctx.values.a)
        ctx.values.a.add(42)
        ctx.values.a.add(101)

    initial_values = DotMap({"a": [33]})
    outputs = hook.testrun(main, initial_values=initial_values)

    assert outputs.values_patches.data != [
        {"op": "remove", "path": "/a"},
        {"op": "add", "path": "/a", "value": [33, 42, 101]},
    ]


def test_values_arrays_are_manipulated_as_whole():
    """
    Since we are not only contrained to "add" and "remove", we also have to treat arrays as whole,
    we remove it first and add new instead of patching it.
    """

    def main(ctx):
        v = DotMap(ctx.values)
        del v.removed
        v.updated = [2, 4, 1, 5, 6, 3]
        v.new = [10, 11, 12]
        v.shrinked = v.shrinked[1:]
        ctx.values = v.toDict()

    initial_values = {
        "removed": [1, 2, 3],
        "updated": [4, 5, 6],
        "shrinked": [7, 8, 9],
    }

    outputs = hook.testrun(main, initial_values=initial_values)

    assert outputs.values_patches.data == [
        {"op": "remove", "path": "/updated"},
        {"op": "add", "path": "/updated", "value": [2, 4, 1, 5, 6, 3]},
        {"op": "remove", "path": "/shrinked"},
        {"op": "add", "path": "/shrinked", "value": [8, 9]},
        {"op": "add", "path": "/new", "value": [10, 11, 12]},
        {"op": "remove", "path": "/removed"},
    ]


def test_internal_patch():
    def main(ctx):
        ctx.values.dummyModuleName.internal.count += 1
        if ctx.values.dummyModuleName.array:
            ctx.values.dummyModuleName.internal.statement = "THE ARRAY IS HERE"
        else:
            ctx.values.dummyModuleName.internal.statement = "NO ARRAY IN CONFIG"

    initial_values = DotMap()
    initial_values.dummyModuleName = {
        "array": [2, 3, 4],
        "internal": {},
        "statement": "c_o_n_f_i_g",
    }

    outputs = hook.testrun(main, initial_values=initial_values)

    assert outputs.values.dummyModuleName.internal.count == 1
    assert outputs.values.dummyModuleName.internal.statement == "THE ARRAY IS HERE"

    assert outputs.values_patches.data == [
        {"op": "add", "path": "/dummyModuleName/internal/count", "value": 1},
        {
            "op": "add",
            "path": "/dummyModuleName/internal/statement",
            "value": "THE ARRAY IS HERE",
        },
    ]
