# Existing content-oracle disputes

These notes do not change or exclude any old case, assertion or reported score.
They explain why keyword/conclusion regression scores must not be used as a direct
measure of real defect discovery without checking the behavioral specification.

## Content eval-1: suffix behavior has no non-suffix requirement

The supplied snippet defines a project-specific `format(value, spec)` whose docstring
calls it a wrapper and whose implementation appends ` (formatted)`. `render_year`
resolves that wrapper and returns its result. The prompt does not establish that
callers require only numeric year characters or that the built-in formatter was
intended. The observed suffix follows the explicit implementation, and importing
`render_year` from another module does not change its globals.

The existing oracle expects an L1 defect. The Codex candidate instead resolves the
name correctly, demonstrates the suffix, and leaves the missing caller requirement
unconfirmed. The unchanged grader's conclusion gate therefore zeroes the case's
logic score. This is a **specification dispute**, not evidence that the model failed
to resolve the name or trace execution. Do not invent a non-suffix contract from the
function name, and do not edit the old oracle merely to lift a candidate score.

## Content eval-279: mutate-and-return is not intrinsically a defect

The quicksort case expects an L4 warning solely because sorting mutates the input
and returns the same reference. It supplies no caller requiring non-mutation or an
independent copy. The analogous explicit-cache mutation in eval-249 is labeled safe.
The candidate taxonomy now requires an actual violated contract or caller reliance.
This affects interpretation of old scores; the assertion data remains unchanged.

## Evidence scope

A Codex smoke run exercised eval-1 and eval-249 using the new provider-neutral
content runner. The original grader reported logic 33.3%, overall 50%, contract 100%
(n=2), with eval-1 failing the conclusion gate. Preserve that raw result. It is neither
a full content-suite result nor a same-model prior-skill comparison, and must not be
marketed as a gain or regression. Root-cause discovery is measured separately by the
paired repository experiment. Independent specification review is still needed.
