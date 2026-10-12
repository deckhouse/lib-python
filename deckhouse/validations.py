#!/usr/bin/env python3
#
# Copyright 2023 Flant JSC Licensed under Apache License 2.0
#


import typing

# What a webhook hands over as warnings or a message: a string, a list of them, or nothing.
Messages = typing.Union[str, typing.Iterable[str], None]


def _strings(values) -> tuple:
    """The non-empty strings of `values`, with lists and tuples among them unpacked."""
    result = []
    for value in values:
        if isinstance(value, (list, tuple)):
            result.extend(_strings(value))
        elif value:
            result.append(value)
    return tuple(result)


class ValidationsCollector:
    """
    Wrapper for the validating feature of Shell Operator.

    https://github.com/flant/shell-operator/blob/main/BINDING_VALIDATING.md
    """

    def __init__(self):
        self._data = []

    def collect(self, payload: dict):
        self._data.append(payload)

    @property
    def data(self):
        """The data is a list of ONLY ONE object, because this object will be a single JSON
        conversion response.

        Returns:
            list: the list of single response
        """
        return self._data

    def allow(self, *warnings: Messages):
        """Allows the request. Each warning is a string or a list of them; empty ones are dropped."""
        warnings = _strings(warnings)
        response = {"allowed": True}
        if warnings:
            response["warnings"] = warnings
        self.collect(response)

    def deny(self, message: Messages = None):
        """Denies the request. A list of messages becomes one message, joined with "; "."""
        messages = _strings([message])
        response = {"allowed": False}
        if messages:
            response["message"] = "; ".join(messages)
        self.collect(response)

    def error(self, message: str):
        self.collect({"allowed": False, "message": f"Internal webhook error: {message}"})
