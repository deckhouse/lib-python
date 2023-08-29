from dotmap import DotMap

from deckhouse import hook


def test_k8s_create():
    def main(ctx: hook.Context):
        ctx.kubernetes.create(
            {
                "kind": "Secret",
                "namespace": "secret-ns",
                "name": "secret-name",
                "data": {},
            }
        )

    outputs = hook.testrun(main)

    expected = {
        "operation": "Create",
        "object": {
            "kind": "Secret",
            "namespace": "secret-ns",
            "name": "secret-name",
            "data": {},
        },
    }

    assert len(outputs.kube_operations.data) == 1
    got = outputs.kube_operations.data[0]
    assert got == expected


def test_k8s_delete():
    def main(ctx: hook.Context):
        ctx.kubernetes.delete(kind="Secret", namespace="secret-ns", name="secret-name")

    outputs = hook.testrun(main)

    expected = {
        "operation": "Delete",
        "kind": "Secret",
        "namespace": "secret-ns",
        "name": "secret-name",
    }

    assert len(outputs.kube_operations.data) == 1
    got = outputs.kube_operations.data[0]
    assert got == expected


def test_k8s_json_patch():
    def main(ctx: hook.Context):
        ctx.kubernetes.json_patch(
            kind="Deployment",
            namespace="default",
            name="nginx",
            patch=[{"op": "replace", "path": "/spec/replicas", "value": 1}],
        )

    outputs = hook.testrun(main)

    expected_patch = {
        "operation": "JSONPatch",
        "kind": "Deployment",
        "namespace": "default",
        "name": "nginx",
        "jsonPatch": [{"op": "replace", "path": "/spec/replicas", "value": 1}],
    }

    assert len(outputs.kube_operations.data) == 1
    got = outputs.kube_operations.data[0]
    assert got == expected_patch


def test_k8s_merge_patch():
    def main(ctx: hook.Context):
        ctx.kubernetes.merge_patch(
            kind="Deployment",
            namespace="default",
            name="nginx",
            patch={"spec": {"replicas": 1}},
        )

    outputs = hook.testrun(main)

    expected_patch = {
        "operation": "MergePatch",
        "kind": "Deployment",
        "namespace": "default",
        "name": "nginx",
        "mergePatch": {"spec": {"replicas": 1}},
    }

    assert len(outputs.kube_operations.data) == 1
    got = outputs.kube_operations.data[0]
    assert got == expected_patch
