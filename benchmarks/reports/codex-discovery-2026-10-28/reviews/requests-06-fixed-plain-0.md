<!-- run a60534f984944dfd9af80984613b6dc5; model gpt-6.1-sol; only temporary source links normalized -->

Found one defect through static review.

**[P2] JSON decoding exceptions lose attached context when pickled with the standard-library JSON backend.**  
Location: [src/requests/exceptions.py:44](https://github.com/psf/requests/blob/3ff3ff21dd45957c9e143cd500291959bb15f690/src/requests/exceptions.py#L44)

- **Trigger:** Construct a `JSONDecodeError` with `request=` or `response=`, then serialize and deserialize it with pickle.
- **Expected:** The restored exception retains that context.
- **Actual consequence:** Both attributes become `None`. Custom instance attributes are also lost. This silently removes diagnostic information when exceptions cross a process boundary or are stored.
- **Evidence:** `JSONDecodeError.__init__` forwards keyword arguments to `RequestException`, which stores the context at lines 19–23. However, `__reduce__` at line 52 returns the backend reducer unchanged. The standard-library JSON reducer supplies reconstruction arguments `(msg, doc, pos)` without instance state. Reconstruction therefore invokes `RequestException.__init__` without context, restoring its `None` defaults. [compat.py:30](https://github.com/psf/requests/blob/96b22fa18c00831656ee4b286bf1c9062459b00a/src/requests/compat.py#L30) establishes that the standard-library backend is used when `simplejson` is unavailable.

This finding concerns explicitly attached context; `Response.json()` already constructs decoding exceptions without it. The reviewed JSON exception tests check inheritance, message content, and `doc`, but do not cover exception state across a pickle round trip.

**Open lead:** Whether the optional `simplejson` backend loses the same state remains unverified; its reducer implementation was not among the inspected workspace files. No additional concrete defects were established.

Verification was limited to static inspection of the supplied workspace. The consequence above is derived from source and Python’s pickle reduction behavior, not a runtime observation. No tests or integration requests were run, no external services or parent directories were accessed, and no files were modified.