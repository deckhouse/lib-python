#!/usr/bin/env python3
#
# Copyright 2022 Flant JSC Licensed under Apache License 2.0
#


class MetricsExporter:
    """
    Wrapper for metrics exporting. Accepts raw dicts and appends them into the metrics file.
    """

    def __init__(self, storage):
        self.storage = storage

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.storage.__exit__(exc_type, exc_value, traceback)

    def export(self, metric: dict):
        self.storage.write(metric)

    def expire_group(self, metric_group: str):
        self.export({"action": "expire", "group": metric_group})
