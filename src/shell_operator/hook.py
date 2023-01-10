#!/usr/bin/env python3
#
# Copyright 2022 Flant JSC Licensed under Apache License 2.0
#

import json
import os
import sys
from dataclasses import dataclass
from typing import Iterable

from dictdiffer import deepcopy
from dotmap import DotMap

from .kubernetes import KubeOperationCollector
from .metrics import MetricsCollector
from .storage import FileStorage
from .values import ValuesPatchesCollector


class Output:
    """
    Container for output means for metrics, kubernetes, and values.

    Metrics, Kubernetes JSON patches and values JSON patches are collected in underlying storages,
    whether shell-operator (or addon-operator) file paths, or into memory.
    """

    # Values with outputs for tests, values patches are less convenient than values
    # themselves.
    values: DotMap = None

    def __init__(self, metrics, kube_operations, values_patches):
        self.metrics = metrics
        self.kube_operations = kube_operations
        self.values_patches = values_patches

    # TODO  logger: --log-proxy-hook-json / LOG_PROXY_HOOK_JSON (default=false)
    #
    # Delegate hook stdout/stderr JSON logging to the hooks and act as a proxy that adds some extra
    # fields before just printing the output. NOTE: It ignores LOG_TYPE for the output of the hooks;
    # expects JSON lines to stdout/stderr from the hooks

    def flush(self):
        file_outputs = (
            ("METRICS_PATH", self.metrics),
            ("KUBERNETES_PATCH_PATH", self.kube_operations),
            ("VALUES_JSON_PATCH_PATH", self.values_patches),
        )

        for path, collector in file_outputs:
            with FileStorage(path) as file:
                for payload in collector.data:
                    file.write(payload)


@dataclass
class Context:
    def __init__(self, binding_context: dict, values: dict, output: Output):
        self.binding_context = binding_context
        self.snapshots = binding_context.get("snapshots", {})
        self.values = DotMap(deepcopy(values))  # DotMap for values.dot.notation
        self.output = output

    @property
    def metrics(self):
        return self.output.metrics

    @property
    def kubernetes(self):
        return self.output.kube_operations

    @property
    def values_patches(self):
        return self.output.values_patches


def read_binding_context_file():
    """
    Iterates over hook contexts in the binding context file.

    :yield ctx: hook binding context
    """
    context_path = os.getenv("BINDING_CONTEXT_PATH")
    with open(context_path, "r", encoding="utf-8") as f:
        context = json.load(f)
    for ctx in context:
        yield ctx


def read_values_file():
    """
    Reads module values from the values file.

    :return values: the dict of the values
    """
    values_path = os.getenv("VALUES_PATH")
    with open(values_path, "r", encoding="utf-8") as f:
        values = json.load(f)
    return values


def __run(func, binding_context: list, initial_values: dict):
    """
    Run the hook function with config. Accepts config path or config text.

    :param func: the function to run
    :param binding_context: the list of hook binding contexts
    :param initial_values: initial values
    :return output: output means with all generated payloads and updated values
    """

    output = Output(
        MetricsCollector(),
        KubeOperationCollector(),
        ValuesPatchesCollector(initial_values),
    )

    if not binding_context:
        binding_context = [{}]

    for bindctx in binding_context:
        hookctx = Context(bindctx, initial_values, output)
        func(hookctx)
        output.values = hookctx.values
        output.values_patches.update(hookctx.values)

    return output


def run(func, configpath=None, config=None):
    """
    Run the hook function with config. Accepts config path or config text.

    :param configpath: path to the hook config file
    :param config: hook config text itself
    """

    if len(sys.argv) > 1 and sys.argv[1] == "--config":
        if config is None and configpath is None:
            raise ValueError("config or configpath must be provided")

        if config is not None:
            print(config)
        else:
            with open(configpath, "r", encoding="utf-8") as cf:
                print(cf.read())

        sys.exit(0)

    binding_context = read_binding_context_file()
    initial_values = read_values_file()

    output = __run(func, binding_context, initial_values)

    output.flush()


def testrun(
    func, binding_context: Iterable = None, initial_values: dict = None
) -> Output:
    """
    Test-run the hook function. Accepts binding context and initial values.

    Returns output means for metrics, kubernetes, values patches, and also modified values for more
    convenient tests.

    :param binding_context: the list of hook binding contexts
    :param initial_values: initial values
    :return: output means for metrics and kubernetes
    """

    output = __run(func, binding_context, initial_values)
    return output
