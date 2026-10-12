#!/usr/bin/env python3
#
# Copyright 2024 Flant JSC Licensed under Apache License 2.0
#

import copy
import sys
import types
import unittest
import typing
from pathlib import Path

from dotmap import DotMap

from . import hook, utils, validations
from .hook import Output


# msg: typing.Tuple[str, ...] | str | None
def __assert_validation(t: unittest.TestCase, o: Output, allowed: bool, msg: typing.Union[typing.Tuple[str, ...], str, None]):
    v = o.validations

    t.assertEqual(len(v.data), 1)

    if allowed:
        t.assertTrue(v.data[0]["allowed"])

        if not msg:
            return

        if isinstance(msg, str):
            t.assertEqual(len(v.data[0]["warnings"]), 1)
            t.assertEqual(v.data[0]["warnings"][0], msg)
        elif isinstance(msg, tuple):
            t.assertEqual(v.data[0]["warnings"], msg)
        else:
            t.fail("Incorrect msg type")
    else:
        if not isinstance(msg, str):
            t.fail("Incorrect msg type")

        t.assertIsNotNone(msg)
        t.assertIsInstance(msg, str)
        t.assertFalse(v.data[0]["allowed"])
        t.assertEqual(v.data[0]["message"], msg)


# msg: typing.Tuple[str, ...] | str | None
def assert_validation_allowed(t: unittest.TestCase, o: Output, msg: typing.Union[typing.Tuple[str, ...], str, None]):
    """
        Assert that validation webhook returns "allowed" result

        Args:
            t (unittest.TestCase): unit test context (self in Test class method)
            o (hook.Output): output from hook.testrun
            msg (any): tuple or str or None, warnings for output, tuple for multiple warnings, str for one warning, None without warnings
    """
    __assert_validation(t, o, True, msg)


def assert_validation_deny(t: unittest.TestCase, o: Output, msg: str):
    """
        Assert that validation webhook returns "deny" result

        Args:
            t (unittest.TestCase): unit test context (self in Test class method)
            o (hook.Output): output from hook.testrun
            msg (str): failed message
    """
    __assert_validation(t, o, False, msg)


def assert_common_resource_fields(t: unittest.TestCase, obj: dict, api_version: str, name: str, namespace: str = ""):
    """
        Assert for object represented as dict api version name and namespace
        This fixture may be useful for conversion webhook tests for checking
            that conversion webhook did not change name and namespace and set valid api version

        Args:
            t (unittest.TestCase): unit test context (self in Test class method)
            obj (hook.Output): output from hook.testrun
            api_version (str): API version for expected object
            name (str): name of expected object
            namespace (str): namespace of expected object
    """

    t.assertIn("apiVersion", obj)
    t.assertEqual(obj["apiVersion"], api_version)

    t.assertIn("metadata", obj)

    t.assertIn("name", obj["metadata"])
    t.assertEqual(obj["metadata"]["name"], name)

    if namespace:
        t.assertIn("namespace", obj["metadata"])
        t.assertEqual(obj["metadata"]["namespace"], namespace)

# res: dict | typing.List[dict] | typing.Callable[[unittest.TestCase, typing.List[dict]], None]
def assert_conversion(t: unittest.TestCase, o: Output, res: typing.Union[dict, typing.List[dict], typing.Callable[[unittest.TestCase, typing.List[dict]], None]], failed_msg: typing.Union[str, None]):
    """
        Assert result of conversion webhook

        Args:
            t (unittest.TestCase): unit test context (self in Test class method)
            o (hook.Output): output from hook.testrun
            res (any): Can be: dict - for one resource convertion, list of dicts for conversion multiple objects per request
                       or function callable[ (unittest.TestCase, typing.List[dict]) -> None ] for assert objects for your manner
            failed_msg (str | None): should present for asserting failed result of webhook
    """

    d = o.conversions.data

    t.assertEqual(len(d), 1)

    if not failed_msg is None:
        t.assertEqual(len(d[0]), 1)
        t.assertEqual(d[0]["failedMessage"], failed_msg)
        return

    if callable(res):
        res(t, d[0]["convertedObjects"])
        return

    expected = res
    if isinstance(res, dict):
        expected = [res]


    t.assertEqual(d[0]["convertedObjects"], expected)


def load_validation_webhook(*paths: typing.Union[str, Path]) -> types.ModuleType:
    """
        Returns the hook webhook-operator renders for a ValidationWebhook as a module, so
        hook.testrun can run its main.

        Args:
            paths: the files of handler.python, in the order the ValidationWebhook joins them
    """
    paths = [Path(p) for p in paths]
    # The names the template has in scope for handler.python.
    module = _new_module(paths, {"Optional": typing.Optional, "DotMap": DotMap, "hook": hook, "validations": validations})

    # The template defines main before handler.python, so a handler could override it.
    module.main = lambda ctx: validations.handle(ctx, module.validate)
    for path in paths:
        exec(compile(path.read_text(), str(path), "exec"), module.__dict__)
    template_main = module.main

    def main(ctx: hook.Context):
        # The template sets keepFullObjectsInMemory: false on every context binding, so the hook
        # gets the jqFilter result only. A snapshot item a test hands over with the full object
        # must not let a handler that reads `object` pass here and fail in the cluster.
        ctx.binding_context = _without_full_objects(ctx.binding_context)
        ctx.snapshots = ctx.binding_context.get("snapshots", {})
        return template_main(ctx)

    module.main = main
    return module


def load_conversion_webhook(crd: str, conversions: typing.Iterable[typing.Tuple[str, str]], *paths: typing.Union[str, Path]) -> types.ModuleType:
    """
        Returns the hook webhook-operator renders for a ConversionWebhook as a module, so
        hook.testrun can run its main with module.config.

        Args:
            crd: the name of the CRD, nodegroups.deckhouse.io
            conversions: the (from, to) version pairs of the resource, ("v1alpha1", "v1")
            paths: the files of handler.python, in the order of the resource
    """
    paths = [Path(p) for p in paths]
    # The names the template has in scope for handler.python.
    module = _new_module(paths, {"typing": typing, "DotMap": DotMap, "hook": hook, "utils": utils})

    # The template pastes the handlers into a utils.BaseConversionHook subclass, indented by four
    # spaces, every line including blank ones and lines inside multi-line strings.
    handlers = "\n".join("\n".join("    " + line for line in p.read_text().split("\n")) for p in paths)
    code = (
        "class Conversion(utils.BaseConversionHook):\n"
        "    def __init__(self, ctx: hook.Context):\n"
        "        super().__init__(ctx)\n"
        + handlers
        + "\n\ndef main(ctx: hook.Context):\n    Conversion(ctx).run()\n"
    )
    exec(compile(code, str(paths[0]), "exec"), module.__dict__)

    group = crd.split(".", 1)[1]
    module.config = "configVersion: v1\nkubernetesCustomResourceConversion:\n" + "".join(
        f"  - name: {source}_to_{target}\n"
        f"    crdName: {crd}\n"
        f"    conversions:\n"
        f"    - fromVersion: {group}/{source}\n"
        f"      toVersion: {group}/{target}\n"
        for source, target in conversions
    )
    return module


def _new_module(paths: typing.List[Path], names: dict) -> types.ModuleType:
    name = "_".join(p.stem for p in paths) + "_hook"
    module = types.ModuleType(name)
    module.__dict__.update(names)
    sys.modules[name] = module
    return module


def _without_full_objects(binding_context):
    plain = copy.deepcopy(binding_context.toDict() if isinstance(binding_context, DotMap) else binding_context)
    for snapshot in (plain.get("snapshots") or {}).values():
        for item in snapshot or []:
            if isinstance(item, dict):
                item.pop("object", None)
    return plain
