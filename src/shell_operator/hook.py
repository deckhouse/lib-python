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
from .storage import FileStorage


@dataclass
class HookContext:
    def __init__(self, binding_context: dict, metrics, kubernetes):
        self.binding_context = binding_context
        self.snapshots = binding_context.get("snapshots", {})
        self.metrics = metrics
        self.kubernetes = kubernetes


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


# TODO --log-proxy-hook-json / LOG_PROXY_HOOK_JSON (default=false)
#   Delegate hook stdout/stderr JSON logging to the hooks and act as a proxy that adds some extra #
#   fields before just printing the output. NOTE: It ignores LOG_TYPE for the output of the hooks; #
#   expects JSON lines to stdout/stderr from the hooks


def bindingcontext(configpath=None, config=None):
    """
    Provides binding context for hook. Accepts config path or config text.

    :param configpath: path to the hook config file
    :param config: hook config text itself

    Example:

     for ctx in bindingcontext(configath="my_hook.yaml")
        do_something(ctx)
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

    metrics = MetricsExporter(FileStorage(os.getenv("METRICS_PATH")))
    kubernetes = KubernetesModifier(FileStorage(os.getenv("KUBERNETES_PATCH_PATH")))
    for ctx in read_binding_context():
        yield HookContext(ctx, metrics, kubernetes)


def run(func, configpath=None, config=None):
    """
    Run the hook function with config. Accepts config path or config text.

    :param configpath: path to the hook config file
    :param config: hook config text itself
    """
    for ctx in bindingcontext(configpath=configpath, config=config):
        func(ctx)
