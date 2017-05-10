from rest_framework import viewsets, filters, renderers
from rest_framework_extensions.mixins import NestedViewSetMixin

from bestiary.serializers import *
from bestiary.pagination import *


# Django REST framework views
class MonsterViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Monster.objects.all()
    renderer_classes = (renderers.BrowsableAPIRenderer, renderers.JSONRenderer)
    serializer_class = MonsterSerializer
    pagination_class = BestiarySetPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('name', 'element', 'archetype', 'base_stars', 'obtainable', 'is_awakened', 'com2us_id', 'family_id')


class MonsterSkillViewSet(NestedViewSetMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Skill.objects.all()
    renderer_classes = (renderers.BrowsableAPIRenderer, renderers.JSONRenderer)
    serializer_class = MonsterSkillSerializer
    pagination_class = BestiarySetPagination


class MonsterLeaderSkillViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LeaderSkill.objects.all()
    renderer_classes = (renderers.BrowsableAPIRenderer, renderers.JSONRenderer)
    serializer_class = MonsterLeaderSkillSerializer
    pagination_class = BestiarySetPagination


class MonsterSkillEffectViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Effect.objects.all()
    renderer_classes = (renderers.BrowsableAPIRenderer, renderers.JSONRenderer)
    serializer_class = MonsterSkillEffectSerializer
    pagination_class = BestiarySetPagination


class MonsterSourceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Source.objects.all()
    renderer_classes = (renderers.BrowsableAPIRenderer, renderers.JSONRenderer)
    serializer_class = MonsterSourceSerializer
    pagination_class = BestiarySetPagination
