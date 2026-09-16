from ipware import get_client_ip


def real_ip_key(group, request):
    """
    Retrieve the real IP address of the client. Used for rate limiting.
    """
    ip, _ = get_client_ip(request)
    return ip or "unknown"
