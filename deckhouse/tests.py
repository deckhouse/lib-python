#!/usr/bin/env python3
#
# Copyright 2024 Flant JSC Licensed under Apache License 2.0
#

import unittest
import typing

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
