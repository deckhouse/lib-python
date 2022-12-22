#!/usr/bin/env python3
#
# Copyright 2022 Flant JSC Licensed under Apache License 2.0
#


class MetricsCollector:
    """
    Wrapper for metrics exporting. Accepts raw dicts and appends them into the metrics file.
    """

    def __init__(self, storage):
        self.storage = storage

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.storage.__exit__(exc_type, exc_value, traceback)

    def collect(self, metric: dict):
        """Collect metric JSON for export.

        Args:
            metric (dict): metric dict, will be serialized into JSON
        """
        self.storage.write(metric)

    def expire(self, group: str):
        """Expire all metrics in the group.

        Args:
            group (str): metric group name
        """
        self.collect({"action": "expire", "group": group})
