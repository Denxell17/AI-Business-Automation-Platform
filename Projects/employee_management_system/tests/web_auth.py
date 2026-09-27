"""CSRF-aware browser authentication helpers for web tests."""

import re


def csrf_token_from_page(client, path: str) -> str:
    response = client.get(path)
    if response.status_code != 200:
        raise AssertionError(
            f"Expected {path} to return 200, got {response.status_code}."
        )
    match = re.search(
        r'name="csrf_token"\s+value="([^"]+)"',
        response.text,
    )
    if match is None:
        raise AssertionError(f"No CSRF token was rendered by {path}.")
    return match.group(1)


def sign_in(client, username: str, password: str, *, follow_redirects=False):
    return client.post(
        "/login",
        data={
            "username": username,
            "password": password,
            "csrf_token": csrf_token_from_page(client, "/login"),
        },
        follow_redirects=follow_redirects,
    )


def sign_out(client, *, follow_redirects=False):
    return client.post(
        "/logout",
        data={"csrf_token": csrf_token_from_page(client, "/")},
        follow_redirects=follow_redirects,
    )
