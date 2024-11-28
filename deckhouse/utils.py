#!/usr/bin/env python3
#
# Copyright 2024 Flant JSC Licensed under Apache License 2.0
#

from .hook import Context


class BaseConversionHook:
    """
        Base class for convertion webhook realisation.
        Usage.
        Create class realisation with methods which named as kubernetesCustomResourceConversion[*].name and
            which get dict resource for conversion and returns tuple (string|None, dict) with result
            if string is not None conversion webhook will return error.

        For example. We have next conversion webhook declaration:
            configVersion: v1
            kubernetesCustomResourceConversion:
            - name: alpha1_to_alpha2
              crdName: nodegroups.deckhouse.io
            conversions:
            - fromVersion: deckhouse.io/v1alpha1
              toVersion: deckhouse.io/v1alpha2

        Then we can create next class for this conversion:

            class NodeGroupConversion(ConversionDispatcher):
                def __init__(self, ctx: Context):
                    super().__init__(ctx)

                def alpha1_to_alpha2(self, o: dict) -> typing.Tuple[str | None, dict]:
                    o["apiVersion"] = "deckhouse.io/v1alpha2"
                    return None, o

        We added method alpha1_to_alpha2 (named as binding name for conversion), get dict for conversion and returns a tuple.

        And in hook file we can use this class in the next way:
            def main(ctx: hook.Context):
                NodeGroupConversion(ctx).run()

            if __name__ == "__main__":
                hook.run(main, config=config)
    """
    def __init__(self, ctx: Context):
        self._binding_context = ctx.binding_context
        self._snapshots = ctx.snapshots
        self.__ctx = ctx


    def run(self):
        binding_name = self._binding_context["binding"]

        try:
            action = getattr(self, binding_name)
        except AttributeError:
            self.__ctx.output.conversions.error("Internal error. Handler for binding {} not found".format(binding_name))
            return

        try:
            errors = []
            from_version = self._binding_context["fromVersion"]
            to_version = self._binding_context["toVersion"]
            for obj in self._binding_context["review"]["request"]["objects"]:
                if from_version != obj["apiVersion"]:
                    self.__ctx.output.conversions.collect(obj)
                    continue

                error_msg, res_obj = action(obj)
                if error_msg is not None:
                    errors.append(error_msg)
                    continue

                assert res_obj["apiVersion"] == to_version

                self.__ctx.output.conversions.collect(res_obj)
            if errors:
                err_msg = ";".join(errors)
                self.__ctx.output.conversions.error(err_msg)
        except Exception as e:
            self.__ctx.output.conversions.error("Internal error: {}".format(str(e)))
            return

