# API reference

Generated from the package's docstrings. It is split in two, and the
difference matters:

- **Public surface.** What each module's `__all__` declares. That is the
  contract: these names do not change without a breaking-change note in
  the changelog.
- **Internals.** The `sinks.sql` submodules, private helpers included.
  Nothing outside `bdns.sync.sinks.sql` should import them and they may
  change without notice. They are documented because the reasoning they
  carry is what explains the design.

Pages are named after the module they document.

For the why rather than the what, see the
[Design](../../explanation/payload-policy.md) pages.
