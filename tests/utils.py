def assert_redirect(response, match):
    redirect_chain = getattr(response, "redirect_chain")

    if not redirect_chain:
        raise AssertionError(f"Response was not redirected {response}")

    assert next(code == 302 and match in url for (url, code) in redirect_chain) is True
