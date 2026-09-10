# What is stored, and what counts as a change

Every record arriving from the API passes two questions before it is
stored, and they are different questions:

1. **What gets stored?** The payload that ends up in the table.
2. **What counts as a change?** What decides whether a new version is
   opened, or only the last-seen timestamp is refreshed.

A `PayloadPolicy` is one entity's answer to both. The whole difficulty of
the module is that the two answers are not symmetric: they can be
decoupled in one direction and not in the other.

## The invariant

> A different hash always means a different stored payload.
> Never the other way round.

Read left to right: if the engine opened a new version, something visible
in the table changed. Anyone reading the history can see what it was.

Read right to left, the implication does **not** hold, and that is
deliberate: two different stored payloads may share a hash. That is
exactly what the hash-only rules do, and it is the safe half.

## Why the order matters

The rules apply in a fixed order, and `prepare` is the only way to use
them. That is not API convenience: it is what stops them being paired
wrongly.

Suppose it were done the other way — drop a field from the stored
payload, but compute the hash over the record **as received**. Then a
change in the dropped field opens a new version whose stored payload is
byte-identical to the one it just closed.

The history claims a change nobody will ever be able to see, because the
evidence was deliberately discarded. It is not a recoverable fault: the
information that justified the version exists nowhere.

That is why `prepare` returns the payload and its hash together, in one
call. Exposing the two steps separately would put within a caller's
reach the one combination that produces unreadable history.

## Why the hash-only rules are safe

`hash_exclude`, `delimited_lists` and `canonical_arrays` go the other
way: they make the hash **coarser** than what is stored.

They declare that two payloads differing only by array order, or by a
shuffled list inside a string, or by a field measured as unstable, are
the same record. They decline to report a difference known to be noise.
They never invent one.

The payload is stored whole, exactly as it arrived. If the rule turns out
to be wrong tomorrow, the data is still there: change the rule and
versioning resumes from the next run. What is lost is history
granularity over the period the rule was active, not the data itself.

That is the criterion for accepting a hash-only rule: **its cost, if it
turns out to be wrong, is recoverable.** A storage rule's is not.

Which rules are declared today, for which entity, and what was measured
to justify each one, is in
[the API's behaviour](bdns-api-behavior.md#spurious-changes). None of
them is a preference; every one is a finding.

## Identity is not policy

Two things stay out of reach of any policy: the fields forming the
natural key, and the registration-date field.

They decide what a record **is** and what links its versions across time.
`check_identity` refuses a policy that tries to drop them.

The asymmetry of cost explains it:

- Changing a hash rule costs storage and noise. Annoying, reversible.
- Changing identity severs a record's past from its future. Old versions
  hang off a key that no longer exists, and new ones start from scratch.
  Nothing recovers that.

Without the natural key a record cannot be versioned at all. Without its
registration date, a windowed run cannot tell a real withdrawal from a
row that simply aged out of the window — that distinction is in
[deletion detection](bdns-api-behavior.md#windowed-deletions).

## Where this lives in the code

- `bdns.sync.policy` — `PayloadPolicy`, `prepare`, `check_identity`.
- `bdns.sync.hashing` — the canonical JSON and the normalizations.
- `bdns.sync.syncers` — the `POLICIES` map, one entry per entity.
