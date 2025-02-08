BLOCKED_HOSTS = {"internal-only.example"}


def is_allowed_url(url: str) -> bool:
    return all(host not in url for host in BLOCKED_HOSTS)
