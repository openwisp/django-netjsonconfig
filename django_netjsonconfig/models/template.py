from django.utils.encoding import python_2_unicode_compatible

from .config import AbstractConfig


@python_2_unicode_compatible
class BaseTemplate(AbstractConfig):
    """
    Abstract model implementing a
    netjsonconfig template
    """
    class Meta:
        abstract = True

    def __str__(self):
        return '[{0}] {1}'.format(self.get_backend_display(), self.name)


class Template(BaseTemplate):
    """
    Concrete Template model
    """
    pass
