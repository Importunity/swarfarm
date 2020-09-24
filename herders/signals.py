from django.core.exceptions import ValidationError
from django.db.models import Count
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver

from .models import MonsterInstance, RuneInstance, RuneBuild, RuneCraftInstance, ArtifactInstance


@receiver(post_save, sender=MonsterInstance)
@receiver(post_save, sender=RuneInstance)
@receiver(post_save, sender=RuneCraftInstance)
def update_profile_date(sender, instance, **kwargs):
    instance.owner.save()


@receiver(m2m_changed, sender=RuneBuild.runes.through)
def validate_rune_build_runes(sender, instance, action, reverse, model, pk_set, **kwargs):
    if action != 'pre_add':
        return

    too_many_slots = model.objects.filter(
        runebuild=instance
    ).exclude(
        pk__in=pk_set
    ).values('slot').annotate(
        slot__count=Count('slot')
    ).filter(
        slot__count__gte=1
    )

    if too_many_slots.exists():
        errors = []
        for result in too_many_slots:
            errors.append(ValidationError(
                {
                    'runes': ValidationError(
                        'Too many runes in slot %(slot)d!',
                        params={'slot': result['slot']}
                    )
                }
            ))

        raise ValidationError(errors)


@receiver(m2m_changed, sender=RuneBuild.artifacts.through)
def validate_rune_build_artifacts(sender, instance, action, reverse, model, pk_set, **kwargs):
    if action != 'pre_add':
        return

    too_many_slots = model.objects.filter(
        runebuild=instance
    ).exclude(
        pk__in=pk_set
    ).values('slot').annotate(
        slot__count=Count('slot')
    ).filter(
        slot__count__gte=1
    )

    if too_many_slots.exists():
        errors = []
        for result in too_many_slots:
            slot_name = ArtifactInstance.SLOT_CHOICES[result['slot']-1][1]
            errors.append(ValidationError(
                {
                    'artifacts': ValidationError(
                        'Too many artifacts in %(slot)s slot!',
                        params={'slot': slot_name}
                    )
                }
            ))

        raise ValidationError(errors)


@receiver(m2m_changed, sender=RuneBuild.runes.through)
@receiver(m2m_changed, sender=RuneBuild.artifacts.through)
def update_rune_build_stats(sender, instance, action, reverse, model, pk_set, **kwargs):
    if action not in ('post_add', 'post_clear', 'post_remove'):
        return

    # Update runebuild stats
    instance.update_stats()
    instance.save()


@receiver(m2m_changed, sender=RuneBuild.runes.through)
@receiver(m2m_changed, sender=RuneBuild.artifacts.through)
def manage_assigned_to(sender, instance, action, reverse, model, pk_set, **kwargs):
    # Update assigned_to field on RuneInstances and ArtifactInstances if this RuneBuild
    # is a monster's default build
    if action not in ('post_add', 'post_clear', 'post_remove'):
        return

    if instance.default_build.exists():
        if action == 'post_remove':
            # Unassign objects which were removed
            model.objects.filter(pk__in=pk_set).update(assigned_to=None)
        elif action == 'post_add':
            # Assign objects which were added
            model.objects.filter(pk__in=pk_set).update(assigned_to=instance.monster)
        elif action == 'post_clear':
            # Remove all objects assigned to the monster
            model.objects.filter(assigned_to=instance.monster).update(assigned_to=None)
