from django.utils.encoding import python_2_unicode_compatible

from .config import AbstractConfig


@python_2_unicode_compatible
class BaseTemplate(AbstractConfig):
    """
    Abstract model implementing a
    netjsonconfig template
    """
    __template__ = True

    class Meta:
        abstract = True

    def __str__(self):
        return '[{0}] {1}'.format(self.get_backend_display(), self.name)

    def save(self, *args, **kwargs):
        """
        modifies status of related configs
        if key attributes have changed (queries the database)
        """
        update_related_config_status = False
        if not self._state.adding:
            current = self.__class__.objects.get(pk=self.pk)
            for attr in ['backend', 'config']:
                if getattr(self, attr) != getattr(current, attr):
                    update_related_config_status = True
                    break
        # save current changes
        super(BaseTemplate, self).save(*args, **kwargs)
        # update relations
        if update_related_config_status:
            self.config_relations.update(status='modified')


class Template(BaseTemplate):
    """
    Concrete Template model
    """
    pass
