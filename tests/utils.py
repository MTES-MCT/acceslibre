from django_otp.plugins.otp_totp.models import TOTPDevice


def assert_redirect(response, match):
    redirect_chain = getattr(response, "redirect_chain")

    if not redirect_chain:
        raise AssertionError(f"Response was not redirected {response}")

    assert next(code == 302 and match in url for (url, code) in redirect_chain) is True


def otp_force_login(client, user):
    client.force_login(user)

    device = TOTPDevice.objects.create(user=user, name="default")

    session = client.session
    session["otp_device_id"] = device.persistent_id
    session.save()

    return device
