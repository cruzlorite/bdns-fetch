# API reference

Generated from the package's docstrings: one page per module, named after
the module it documents.

Every page shows everything the module defines, private helpers
included. What tells them apart is the name:

- **No leading underscore**: meant to be used from outside the module.
  What the module's `__all__` also declares is the contract: those names
  do not change without a breaking-change note in the changelog.
- **Leading underscore** (`_apply`, `_order_independent`…): internals.
  Nothing outside the module should import them, and they may change
  without notice. They are documented because the reasoning they carry
  is what explains the design.

For the why rather than the what, see the
[Explanation](../../explanation/payload-policy.md) pages.
