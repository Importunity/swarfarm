from rest_framework.renderers import BrowsableAPIRenderer


class NoFormBrowsableAPIRenderer(BrowsableAPIRenderer):
    # Disables form rendering in BrowsableAPIRenderer to eliminate query explosions
    # caused by gathering data for related fields form options.
    # JSON POST form is still available.
    def get_rendered_html_form(self, *args, **kwargs):
        return None
