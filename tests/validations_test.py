from deckhouse import hook, validations


def run(handler):
    return hook.testrun(handler).validations.data


def test_allow():
    assert run(lambda ctx: ctx.output.validations.allow()) == [{"allowed": True}]


def test_allow_with_warnings():
    data = run(lambda ctx: ctx.output.validations.allow("first", "second"))
    assert data == [{"allowed": True, "warnings": ("first", "second")}]


def test_allow_with_a_list_of_warnings():
    data = run(lambda ctx: ctx.output.validations.allow(["first", "second"], "third"))
    assert data == [{"allowed": True, "warnings": ("first", "second", "third")}]


def test_allow_drops_empty_warnings():
    for warnings in [(None,), ("",), ([],), ([None, ""],)]:
        assert run(lambda ctx: ctx.output.validations.allow(*warnings)) == [{"allowed": True}]


def test_deny():
    data = run(lambda ctx: ctx.output.validations.deny("not allowed"))
    assert data == [{"allowed": False, "message": "not allowed"}]


def test_deny_joins_a_list_of_messages():
    data = run(lambda ctx: ctx.output.validations.deny(["first", "", "second"]))
    assert data == [{"allowed": False, "message": "first; second"}]


def test_deny_without_a_message():
    for message in [None, "", []]:
        assert run(lambda ctx: ctx.output.validations.deny(message)) == [{"allowed": False}]


def test_error_is_a_denial_with_the_message():
    # shell-operator reads the reason from "message"; any other key is dropped and the
    # requester sees a denial without a reason.
    data = run(lambda ctx: ctx.output.validations.error("snapshot is missing"))
    assert data == [{"allowed": False, "message": "Internal webhook error: snapshot is missing"}]


def test_handle_answers_with_the_result_of_validate():
    def main(ctx):
        validations.handle(ctx, lambda bc: (bc.warnings, True))

    data = hook.testrun(main, [{"warnings": ["first", "second"]}]).validations.data
    assert data == [{"allowed": True, "warnings": ("first", "second")}]
