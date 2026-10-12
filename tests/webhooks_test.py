import textwrap

from deckhouse import hook, tests


def write(tmp_path, name, source):
    path = tmp_path / name
    path.write_text(textwrap.dedent(source))
    return path


def validations(module, binding_context):
    return hook.testrun(module.main, [binding_context]).validations.data


def test_validation_webhook_passes_the_binding_context_as_dotmap(tmp_path):
    path = write(tmp_path, "check.py", '''
        import typing

        def validate(ctx: DotMap) -> typing.Tuple[Optional[str], bool]:
            if ctx.review.request.name == "bad":
                return "bad name", False
            return None, True
    ''')
    module = tests.load_validation_webhook(path)
    assert validations(module, {"review": {"request": {"name": "good"}}}) == [{"allowed": True}]
    assert validations(module, {"review": {"request": {"name": "bad"}}}) == [{"allowed": False, "message": "bad name"}]


def test_validation_webhook_joins_files_in_order(tmp_path):
    first = write(tmp_path, "common.py", '''
        WARNINGS = ["first", "second"]
    ''')
    second = write(tmp_path, "check.py", '''
        def validate(ctx):
            return WARNINGS, True
    ''')
    module = tests.load_validation_webhook(first, second)
    assert validations(module, {}) == [{"allowed": True, "warnings": ("first", "second")}]


def test_validation_webhook_turns_an_exception_into_an_error(tmp_path):
    path = write(tmp_path, "check.py", '''
        def validate(ctx):
            raise KeyError("spec")
    ''')
    data = validations(tests.load_validation_webhook(path), {})
    assert data == [{"allowed": False, "message": "Internal webhook error: 'spec'"}]


def test_validation_webhook_drops_full_objects_from_snapshots(tmp_path):
    # webhook-operator sets keepFullObjectsInMemory: false, so the hook sees filterResult only.
    path = write(tmp_path, "check.py", '''
        def validate(ctx):
            item = ctx.snapshots.pods[0]
            return None, "object" not in item.toDict() and item.filterResult == 1
    ''')
    binding_context = {"snapshots": {"pods": [{"object": {"kind": "Pod"}, "filterResult": 1}]}}
    assert validations(tests.load_validation_webhook(path), binding_context) == [{"allowed": True}]


def test_conversion_webhook(tmp_path):
    path = write(tmp_path, "conversion.py", '''
        def v1alpha1_to_v1(self, o: dict) -> typing.Tuple[typing.Optional[str], dict]:
            """A docstring
            on two lines."""
            o["apiVersion"] = "deckhouse.io/v1"
            return None, o
    ''')
    module = tests.load_conversion_webhook("things.deckhouse.io", [("v1alpha1", "v1")], path)
    assert "fromVersion: deckhouse.io/v1alpha1" in module.config

    out = hook.testrun(module.main, [{
        "binding": "v1alpha1_to_v1",
        "fromVersion": "deckhouse.io/v1alpha1",
        "toVersion": "deckhouse.io/v1",
        "review": {"request": {"objects": [{"apiVersion": "deckhouse.io/v1alpha1", "kind": "Thing"}]}},
    }])
    assert out.conversions.data == [{"convertedObjects": [{"apiVersion": "deckhouse.io/v1", "kind": "Thing"}]}]
