# Configuration

`bootstrap.json` parameterizes the human authority, display names, narrow and
broad verification commands, optional recognition wording, and the current
runtime-selected model fallback. `writer_owner_count` is an integer only;
booleans are invalid. Bucky is never counted.

`catalog` is a closed, read-only snapshot with source exactly
`active-runtime:model/list`, captured from the runtime's model/list response.
Every pair is the exact `model` family/ID string and `effort` advertised there;
pairs are unique and no spawn result may be used as provenance. For the current
runtime snapshot, use the advertised `gpt-5.6-sol` and `gpt-5.6-terra` families
with the advertised low, medium, high, xhigh, max, and ultra efforts. Luna is
not in that snapshot, so its status is `not_advertised_in_this_runtime` (not a
global-availability claim).

The following values are fixed and must match exactly: one writer, safe
handoff, redaction, explicit routing, and a fixed sandbox policy. A model
selection records a local runtime decision only; it must never state that Luna
is globally unavailable based on one spawn result. `tightly_specified` is an
explicit JSON boolean, not free text. The derived recommendation is
`gpt-5.6-luna` at `xhigh` only when that exact pair is advertised and the
boolean is true; otherwise it is `gpt-5.6-terra` at an advertised effort. The
requested pair and recommendation must match. At active count one the selected
current pair must also match; at count zero the prior current pair can remain
while the next requested pair is recorded.

The JSON result always has exactly `mode`, `apply`, `created`, `unchanged`,
`conflicts`, and `errors`, with repository-relative paths. It exits zero only
when conforming, one for validation or collision failure, and two for invalid
arguments.
