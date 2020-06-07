from celery.result import AsyncResult
from django.db.models import Q
from django_filters import rest_framework as filters
from rest_framework import viewsets, status
from rest_framework.filters import OrderingFilter
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from herders.api_filters import SummonerFilter, MonsterInstanceFilter, RuneInstanceFilter, TeamFilter
from herders.pagination import *
from herders.permissions import *
from herders.serializers import *
from .profile_parser import validate_sw_json
from .tasks import com2us_data_import


class SummonerViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().select_related('summoner').order_by('pk')
    pagination_class = PublicListPagination
    permission_classes = [IsSelfOrPublic]
    throttle_scope = 'registration'
    lookup_field = 'username'
    lookup_url_kwarg = 'pk'
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = SummonerFilter

    def get_queryset(self):
        queryset = super(SummonerViewSet, self).get_queryset()

        if not self.request.user.is_superuser and self.action == 'list':
            if self.request.user.is_authenticated:
                # Include current user into results whether or not they are public
                queryset = queryset.filter(Q(summoner__public=True) | Q(pk=self.request.user.pk))
            else:
                queryset = queryset.filter(summoner__public=True)

        return queryset

    def get_serializer_class(self):
        profile_name = self.kwargs.get('pk')
        is_authorized = self.request.user.username == profile_name

        if (is_authorized or self.request.user.is_superuser) or self.action == 'create':
            return FullUserSerializer
        else:
            return SummonerSerializer


class GlobalMonsterInstanceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MonsterInstance.objects.filter(owner__public=True).select_related(
        'monster',
        'owner__user',
    ).prefetch_related(
        'runeinstance_set',
        'runeinstance_set__owner__user',
    ).order_by()
    serializer_class = MonsterInstanceSerializer
    permission_classes = [AllowAny]
    pagination_class = PublicListPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = MonsterInstanceFilter


class GlobalRuneInstanceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RuneInstance.objects.filter(owner__public=True).select_related(
        'owner',
        'owner__user',
        'assigned_to',
    ).order_by()
    serializer_class = RuneInstanceSerializer
    permission_classes = [AllowAny]
    pagination_class = PublicListPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = RuneInstanceFilter


class ProfileItemMixin(viewsets.GenericViewSet):
    pagination_class = PublicListPagination
    permission_classes = [IsOwner]

    def get_queryset(self):
        queryset = super(ProfileItemMixin, self).get_queryset()
        username = self.kwargs.get('user_pk')

        if username is None:
            return queryset.none()

        queryset = queryset.filter(owner__user__username=username)

        if not self.request.user.is_superuser and self.action == 'list':
            if self.request.user.is_authenticated:
                # Include active user into results whether or not they are public so they can view themselves
                queryset = queryset.filter(Q(owner__public=True) | Q(owner=self.request.user.summoner))
            else:
                queryset = queryset.filter(owner__public=True)

        return queryset


class StorageViewSet(ProfileItemMixin, viewsets.ModelViewSet):
    queryset = Storage.objects.all().select_related('owner', 'owner__user')
    serializer_class = StorageSerializer

    def get_object(self):
        username = self.kwargs.get('user_pk')
        filter_kwargs = {'owner__user__username': username}
        queryset = self.filter_queryset(self.get_queryset())
        obj = get_object_or_404(queryset, **filter_kwargs)

        return obj


class RuneBuildViewSet(ProfileItemMixin, viewsets.ModelViewSet):
    queryset = RuneBuild.objects.all().select_related(
        'owner',
        'owner__user'
    ).prefetch_related(
        'runes',
        'runes__owner',
        'runes__owner__user'
    ).order_by()
    serializer_class = RuneBuildSerializer


class MonsterInstanceViewSet(ProfileItemMixin, viewsets.ModelViewSet):
    queryset = MonsterInstance.objects.all().select_related(
        'owner',
        'owner__user',
        'monster',
        'default_build',
        'rta_build'
    ).prefetch_related(
        'tags',
        'default_build__runes',
        'rta_build__runes',
    )
    filter_backends = (filters.DjangoFilterBackend, OrderingFilter)
    filter_class = MonsterInstanceFilter
    ordering_fields = (
        'stars',
        'level',
        'created',
        'base_attack',
        'rune_attack',
        'base_defense',
        'rune_defense',
        'base_speed',
        'rune_speed',
        'base_crit_rate',
        'rune_crit_rate',
        'base_crit_damage',
        'rune_crit_damage',
        'base_resistance',
        'rune_resistance',
        'base_accuracy',
        'rune_accuracy',
        'avg_efficiency',
        'fodder',
        'in_storage',
        'ignore_for_fusion',
        'priority',
        'monster__com2us_id',
        'monster__family_id',
        'monster__name',
        'monster__element',
        'monster__archetype',
        'monster__base_stars',
        'monster__natural_stars',
        'monster__can_awaken',
        'monster__is_awakened',
        'monster__base_hp',
        'monster__base_attack',
        'monster__base_defense',
        'monster__speed',
        'monster__crit_rate',
        'monster__crit_damage',
        'monster__resistance',
        'monster__accuracy',
        'monster__raw_hp',
        'monster__raw_attack',
        'monster__raw_defense',
        'monster__max_lvl_hp',
        'monster__max_lvl_attack',
        'monster__max_lvl_defense',
    )

    def get_serializer_class(self):
        profile_name = self.kwargs.get('pk')
        is_authorized = self.request.user.username == profile_name

        if (is_authorized or self.request.user.is_superuser) or self.action == 'create':
            return MonsterInstanceSerializer
        else:
            return PublicMonsterInstanceSerializer


class RuneInstanceViewSet(ProfileItemMixin, viewsets.ModelViewSet):
    queryset = RuneInstance.objects.all().select_related(
        'owner__user',
        'assigned_to',
    )
    serializer_class = RuneInstanceSerializer
    filter_backends = (filters.DjangoFilterBackend, OrderingFilter)
    filter_class = RuneInstanceFilter
    ordering_fields = (
        'type',
        'level',
        'stars',
        'slot',
        'quality',
        'original_quality',
        'assigned_to',
        'main_stat',
        'innate_stat',
        'marked_for_sale',
    )


class RuneCraftInstanceViewSet(ProfileItemMixin, viewsets.ModelViewSet):
    serializer_class = RuneCraftInstanceSerializer


class BuildingViewSet(ProfileItemMixin, viewsets.ModelViewSet):
    queryset = BuildingInstance.objects.all().select_related(
        'building',
        'owner',
        'owner__user',
    )
    serializer_class = BuildingInstanceSerializer


class MonsterPieceViewSet(ProfileItemMixin, viewsets.ModelViewSet):
    queryset = MonsterPiece.objects.all().select_related(
        'owner',
        'owner__user',
    )
    serializer_class = MonsterPieceSerializer


class TeamGroupViewSet(ProfileItemMixin, viewsets.ModelViewSet):
    queryset = TeamGroup.objects.all().select_related(
        'owner',
        'owner__user',
    ).prefetch_related(
        'team_set',
    )
    serializer_class = TeamGroupSerializer


class TeamViewSet(ProfileItemMixin, viewsets.ModelViewSet):
    queryset = Team.objects.all().select_related('group', 'leader').prefetch_related('leader__runeinstance_set', 'roster', 'roster__runeinstance_set')
    serializer_class = TeamSerializer
    renderer_classes = [JSONRenderer]  # Browseable API causes major query explosion when trying to generate form options.
    filter_backends = (filters.DjangoFilterBackend, OrderingFilter)
    filter_class = TeamFilter

    def get_queryset(self):
        # Team objects do not have an owner field, so we must go through the group owner for filtering
        queryset = super(ProfileItemMixin, self).get_queryset()
        summoner_name = self.kwargs.get('user_pk')

        if summoner_name is not None:
            queryset = queryset.filter(group__owner__user__username=summoner_name)

        if not self.request.user.is_superuser and self.action == 'list':
            if self.request.user.is_authenticated:
                # Include active user into results whether or not they are public so they can view themselves
                queryset = queryset.filter(Q(group__owner__public=True) | Q(group__owner=self.request.user.summoner))
            else:
                queryset = queryset.filter(group__owner__public=True)

        return queryset


class ProfileJsonUpload(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    default_import_options = {
        'clear_profile': False,
        'default_priority': '',
        'lock_monsters': True,
        'minimum_stars': 1,
        'ignore_silver': False,
        'ignore_material': False,
        'except_with_runes': True,
        'except_light_and_dark': True,
        'except_fusion_ingredient': True,
        'delete_missing_monsters': 1,
        'delete_missing_runes': 1,
        'ignore_validation_errors': False
    }

    def create(self, request, *args, **kwargs):
        errors = []
        validation_failures = []

        schema_errors, validation_errors = validate_sw_json(request.data, request.user.summoner)

        if schema_errors:
            errors.append(schema_errors)

        if validation_errors:
            validation_failures = "Uploaded data does not match previously imported data. To override, set import preferences to ignore validation errors and import again."

        import_options = request.user.summoner.preferences.get('import_options', self.default_import_options)

        if not errors and (not validation_failures or import_options['ignore_validation_errors']):
            # Queue the import
            task = com2us_data_import.delay(request.data, request.user.summoner.pk, import_options)
            return Response({'job_id': task.task_id})

        elif validation_failures:
            return Response({'validation_error': validation_failures}, status=status.HTTP_409_CONFLICT)
        else:
            return Response({'error': errors}, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, user_pk=None, pk=None):
        task = AsyncResult(pk)

        if task:
            try:
                return Response({
                    'status': task.status,
                })
            except:
                return Response({
                    'status': 'error',
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)