# Source: https://stackoverflow.com/questions/74368412/exclude-some-urls-in-django-for-sentry-performance-tracing

# For the following routes prefixes, we will reduce the sampling rate
restricted_urls_starting_with = ["/uuid/", "/api/erps"]


def custom_traces_sample_rate(ctx):
    if ctx["parent_sampled"] is not None:
        return ctx["parent_sampled"]

    op = ctx["transaction_context"]["op"]
    if "wsgi_environ" in ctx:
        url = ctx["wsgi_environ"].get("PATH_INFO", "")
    elif "asgi_scope" in ctx:
        url = ctx["asgi_scope"].get("path", "")
    else:
        url = ""

    if url and op == "http.server":
        if any([url.startswith(u) for u in restricted_urls_starting_with]):
            return 0.01
    return 0.1
