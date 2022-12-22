#!/usr/bin/env python3
#
# Copyright 2022 Flant JSC Licensed under Apache License 2.0
#

import json
import os
import sys
from dataclasses import dataclass
from typing import Iterable

from .kubernetes import KubernetesModifier
from .metrics import MetricsCollector
from .storage import FileStorage, MemStorage


@dataclass
class Output:
    metrics: MetricsCollector
    kubernetes: KubernetesModifier

    # TODO  --log-proxy-hook-json / LOG_PROXY_HOOK_JSON (default=false) Delegate hook stdout/stderr
    # JSON logging to the hooks and act as a proxy that adds some extra fields before just printing
    # the output. NOTE: It ignores LOG_TYPE for the output of the hooks; expects JSON lines to
    # stdout/stderr from the hooks


@dataclass
class Context:
    def __init__(self, binding_context: dict, output: Output):
        self.binding_context = binding_context
        self.snapshots = binding_context.get("snapshots", {})
        self.output = output


def read_binding_context():
    """
    Iterates over hook contexts in the binding context file.

    Yields:
        _type_: dict
    """
    context_path = os.getenv("BINDING_CONTEXT_PATH")
    with open(context_path, "r", encoding="utf-8") as f:
        context = json.load(f)
    for ctx in context:
        yield ctx


def __run(func, binding_context, output):
    """
    Run the hook function with config. Accepts config path or config text.

    :param func: the function to run
    :param binding_context: the list of hook binding contexts
    :param output: output means for metrics and kubernetes
    """

    for bindctx in binding_context:
        hookctx = Context(bindctx, output)
        func(hookctx)


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

    output = Output(
        MetricsCollector(FileStorage(os.getenv("METRICS_PATH"))),
        KubernetesModifier(FileStorage(os.getenv("KUBERNETES_PATCH_PATH"))),
    )

    binding_context = read_binding_context()

    __run(func, binding_context, output)


def testrun(func, binding_context: Iterable) -> Output:
    """
    Test-run the hook function with config. Accepts config path or config text.

    Returns output means for metrics and kubernetes.

    :param binding_context: the list of hook binding contexts
    :return: output means for metrics and kubernetes
    """

    output = Output(
        MetricsCollector(MemStorage()),
        KubernetesModifier(MemStorage()),
    )

    __run(func, binding_context, output)

    return output
