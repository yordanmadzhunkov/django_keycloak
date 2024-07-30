from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth.models import User

from django_q.tasks import async_task

from vei_platform.models.profile import UserProfile
from vei_platform.models.legal import LegalEntity, add_legal_entity
from vei_platform.models.factory import ElectricityFactory


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    if UserProfile.objects.get(user=instance) is None:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=LegalEntity)
def legal_entity_post_save(sender, **kwargs):
    instance = kwargs.get("instance")
    tax_id = instance.tax_id
    factories_for_upgrade = ElectricityFactory.objects.filter(tax_id=tax_id).filter(
        primary_owner=None
    )
    for factory in factories_for_upgrade:
        factory.primary_owner = instance
        factory.save()


@receiver(post_save, sender=ElectricityFactory)
def electical_factory_post_save(sender, **kwargs):
    instance = kwargs.get("instance")
    if instance.primary_owner is None:
        owner_name = instance.owner_name
        tax_id = instance.tax_id
        print("Search for name='%s' or tax_id=%s" % (owner_name, tax_id))
        legal_entities = LegalEntity.objects.filter(tax_id=tax_id)
        if len(legal_entities) > 0:
            legal_entity = legal_entities[0]
            instance.primary_owner = legal_entity
            print("Saving the instance with new primary owner = %s" % str(legal_entity))
            instance.save()
        else:
            async_task(
                "vei_platform.tasks.scripe_factory_legal_entity",
                instance,
                task_name="LegalEntity-for-%s" % instance.name,
                hook=add_legal_entity,
            )
