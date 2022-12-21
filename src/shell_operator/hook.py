#!/usr/bin/env python3
#
# Copyright 2022 Flant JSC Licensed under Apache License 2.0
#

import json
import os
import sys
from dataclasses import dataclass

from .kubernetes import KubernetesModifier
from .metrics import MetricsExporter


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


@dataclass
class HookContext:
    def __init__(self, binding_context: dict, metrics=None, kubernetes=None):
        self.binding_context = binding_context
        self.snapshots = binding_context.get("snapshots", {})
        self.metrics = MetricsExporter() if metrics is None else metrics
        self.kubernetes = KubernetesModifier() if kubernetes is None else kubernetes


# TODO --log-proxy-hook-json / LOG_PROXY_HOOK_JSON (default=false)
#   Delegate hook stdout/stderr JSON logging to the hooks and act as a proxy that adds some extra #
#   fields before just printing the output. NOTE: It ignores LOG_TYPE for the output of the hooks; #
#   expects JSON lines to stdout/stderr from the hooks


def bindingcontext(configpath):
    """
    Provides binding context for hook.

    Example:

     for ctx in bindingcontext("my_hook.yaml")
        do_something(ctx)
    """
    if len(sys.argv) > 1 and sys.argv[1] == "--config":
        with open(configpath, "r", encoding="utf-8") as cf:
            print(cf.read())
            sys.exit(0)

    for ctx in read_binding_context():
        yield HookContext(ctx)


def run(func, configpath):
    """
    Run the hook function with config.
    """
    for ctx in bindingcontext(configpath):
        func(ctx)
