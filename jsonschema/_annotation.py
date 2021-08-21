"""
Support for JSON Schema annotation collection.
"""

from collections import deque

import attr

from jsonschema._utils import __no_init_subclass__


@attr.s
class Annotator:
    """
    An annotator supervises validation of an instance, annotating as it goes.

    Whereas validators, type checkers, format checkers and the like
    are generally stateless, an annotator is *stateful*. It tracks
    the incremental progress as validation –or more broadly pure
    annotation– of an instance is progressing.
    """

    _validator = attr.ib(
        repr=lambda validator: f"<{validator.__class__.__name__}>",
        kw_only=True,
    )

    def __attrs_post_init__(self):
        self._scope_stack = deque([self._validator.ID_OF(self._validator.schema)])

    def descend(self, instance, schema, path=None, schema_path=None):
        validator = attr.evolve(self._validator, schema=schema)
        for error in validator.iter_errors(instance):
            if path is not None:
                error.path.appendleft(path)
            if schema_path is not None:
                error.schema_path.appendleft(schema_path)
            yield error

    __init_subclass__ = __no_init_subclass__

    # TODO: IMPROVEME / belongs on ref resolver?
    def scopes_moving_outward(self):
        yield self.resolver.resolution_scope, self._validator.schema
        for each in reversed(self.resolver._scopes_stack[1:]):
            yield self.resolver.resolve(each)

    def descend_at_ref(self, instance, ref):
        scope, resolved = self._validator.resolver.resolve(
            ref=ref,
            resolution_scope=self._scope_stack[-1],
        )
        self._scope_stack.append(scope)
        yield from self.descend(instance=instance, schema=resolved)
        self._scope_stack.pop()

    # TODO: REMOVEME
    @property
    def format_checker(self): return self._validator.format_checker
    @property
    def is_valid(self): return self._validator.is_valid
    @property
    def is_type(self): return self._validator.is_type
