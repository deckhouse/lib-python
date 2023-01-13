#!/usr/bin/env python3
#
# Copyright 2023 Flant JSC Licensed under Apache License 2.0
#

from typing import Iterable

from dictdiffer import deepcopy, diff


class ValuesPatchesCollector:
    """
    Wrapper for the values manipulations (JSON patches)
    """

    def __init__(self, values: dict):
        self.initial_values = deepcopy(values)
        self.data = []

    def collect(self, payload: dict):
        self.data.append(payload)

    def update(self, updated_values: dict):
        for patch in values_json_patches(self.initial_values, updated_values):
            self.collect(patch)


def values_json_patches(initial_values: dict, updated_values: dict):
    changes = diff(
        initial_values,
        updated_values,
        dot_notation=False,  # always return path as list
        expand=True,  # do not compact values in single operation
    )
    for change in changes:
        yield json_patch(change)


def json_patch(change):
    """
    Trtansform dictdiffer change to JSON patch.
    https://jsonpatch.com/#operations
    """
    op, path_segments, values = change

    if op == "add":
        #   op    |______path_________|   value
        #    |    |                   |  /
        # ('add', ['x', 'y', 'a'], [(2, 2)])

        key, value = values[0]
        path = json_path(path_segments + [key])
        return {"op": "add", "path": path, "value": value}

    if op == "change":
        #   op       |______path______|  from  to
        #    |       |                |   |   /
        # ('change', ['x', 'y', 'a', 0], (1, 0))

        value = values[1]
        path = json_path(path_segments)
        return {"op": "replace", "path": path, "value": value}

    if op == "remove":
        #   op       |______path_____|     value
        #    |       |               |    /
        # ('remove', ['x', 'y'], [('t', 0)])

        key = values[0][0]
        path = json_path(path_segments + [key])
        return {"op": "remove", "path": path}

    raise ValueError(f"Unknown patch operation: {op}")


def json_path(path: Iterable):
    return "/" + "/".join([str(p) for p in path])
