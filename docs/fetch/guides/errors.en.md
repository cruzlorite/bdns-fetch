# Errors and retries

What the client retries, what it does not, and how to react to what reaches your code.

## What is retried automatically

| Failure | Retried? |
|---|---|
| Network error, timeout | Yes |
| HTTP `429` (rate limit) | Yes, honouring `Retry-After` when sent |
| HTTP `500`, `502`, `503`, `504` | Yes |
| `ERR_MANTENIMIENTO_BBDD` code, with any status | Yes |
| Any other error (`400`, `404`, `ERR_VALIDACION`...) | No: repeating a bad request does not fix it |

The wait starts at `wait_time` seconds and doubles on each retry, plus random jitter, up to 60 s. `max_retries` counts retries **after** the first attempt; 0 disables them.

```python
client = BDNSClient(max_retries=5, wait_time=10)   # for an unattended process
```

```console
$ bdns-fetch --max-retries 5 --wait-time 10 concesiones-busqueda ...
```

For a nightly job that should not die over a rough patch of a few minutes: 5 retries starting at 10 s wait 10, 20, 40, 60 and 60 s (plus jitter), riding out about 3-4 minutes of trouble per request.

## What reaches your code

Every API error is a [[`BDNSError`][bdns.fetch.exceptions.BDNSError]][bdns.fetch.exceptions.BDNSError]:

| Attribute | Content |
|---|---|
| `message` | What the API said, usually in Spanish |
| `status_code` | HTTP status |
| `code` | The API's error code (`ERR_VALIDACION`...), if any |
| `url` | The requested URL |
| `details` | Status, URL, headers and the start of the body, for logs |

Transient ones that ran out of retries are [`BDNSTransientError`][bdns.fetch.exceptions.BDNSTransientError], a subclass:

```python
from bdns.fetch import BDNSError, BDNSTransientError

try:
    records = list(client.fetch_concesiones_busqueda(**date_range))
except BDNSTransientError:
    schedule_retry_later()
except BDNSError as error:
    if error.code == "ERR_VALIDACION":
        fix_parameters(error.message)
    else:
        raise
```

Network errors that ran out of retries arrive as the original `requests` exception (`ConnectionError`, `Timeout`).

!!! warning "Iterators fail when iterated"
    A search method returns a lazy iterator: the error is raised while consuming it, not when calling the method. Wrap the loop, not the call.

## From the CLI

The CLI turns any [`BDNSError`][bdns.fetch.exceptions.BDNSError] into a message and exit code 1, with a hint depending on the kind of error. `--verbose` adds the response details and a log line per HTTP request.
