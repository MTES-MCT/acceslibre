from django import template

register = template.Library()


@register.filter(name="active_compte_section")
def active_compte_section(path, test):
    # There should REALLY be a way to retrieve a route name from a request. sigh.
    # So. Don't forget to update this code whenever we update these urls in erp.urls.
    active = any(
        [
            test == "mon_compte" and path == "/mon_compte/",
            test == "mes_erps" and path == "/mon_compte/erps/",
            test == "mot_de_passe"
            and path
            in [
                "/accounts/password_change/",
                "/accounts/password_change/done/",
                "/admin/password_change/",
                "/admin/password_change/done/",
            ],
        ]
    )
    if active:
        return "active"
    else:
        return ""


@register.filter(name="addclass")
def addclass(value, arg):
    return value.as_widget(attrs={"class": arg})
