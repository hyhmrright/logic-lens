<!-- run 0fad2ed7b63c48ebb66fae2e97709fa7; model gpt-6.1-sol; only temporary source links normalized -->

Found one low-priority edge-case defect by static inspection. I did not establish a failure in ordinary Requests-generated request objects.

**Defect: an explicitly supplied falsey request can be overwritten.**  
In [exceptions.py:21](https://github.com/psf/requests/blob/3ff3ff21dd45957c9e143cd500291959bb15f690/src/requests/exceptions.py#L21), the constructor stores `request`, then uses `not self.request` to decide whether to replace it with `response.request`.

- **Trigger:** supply both a response and a request object whose `__bool__` returns `False` or whose `__len__` returns zero—for example, a custom `PreparedRequest` subclass.
- **Expected:** preserve the explicitly supplied request; infer one from the response when `request` is absent or `None`.
- **Actual, derived from the source:** the explicit request is replaced with `response.request`, potentially becoming `None` or referring to a different request. Exception handlers inspecting `error.request` therefore lose the supplied context.
- **Scope:** ordinary `PreparedRequest` objects do not define falsey behavior. The supplied callers do not demonstrate this trigger, so the finding concerns custom request objects and direct exception construction.

**Open lead: JSON exception serialization may discard context.**  
[exceptions.py:44](https://github.com/psf/requests/blob/3ff3ff21dd45957c9e143cd500291959bb15f690/src/requests/exceptions.py#L44) delegates serialization entirely to the selected JSON backend. That addresses reconstruction arguments, but whether `request`, `response`, and additional attributes survive depends on the backend’s reducer. [compat.py:30](https://github.com/psf/requests/blob/96b22fa18c00831656ee4b286bf1c9062459b00a/src/requests/compat.py#L30) selects external `json` or `simplejson` implementations whose reducer bodies are not supplied here. The inspected tests check JSON exception compatibility and document preservation, but do not establish exception-state preservation through pickling. This remains unconfirmed.

Verification was limited to static inspection using five read-only shell calls. No runtime or integration tests were run, no files were modified, and no external services were accessed.