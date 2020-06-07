import uuid
from collections import OrderedDict
from math import floor, ceil

from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField, JSONField
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, Count, Avg
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe
from timezone_field import TimeZoneField

from bestiary.models import base, Monster, Building, Level, Rune, RuneCraft

from django.db import connection

# Individual user/monster collection models
class Summoner(models.Model):
    SERVER_GLOBAL = 0
    SERVER_EUROPE = 1
    SERVER_ASIA = 2
    SERVER_KOREA = 3
    SERVER_JAPAN = 4
    SERVER_CHINA = 5

    SERVER_CHOICES = [
        (SERVER_GLOBAL, 'Global'),
        (SERVER_EUROPE, 'Europe'),
        (SERVER_ASIA, 'Asia'),
        (SERVER_KOREA, 'Korea'),
        (SERVER_JAPAN, 'Japan'),
        (SERVER_CHINA, 'China'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    summoner_name = models.CharField(max_length=256, null=True, blank=True)
    com2us_id = models.BigIntegerField(default=None, null=True, blank=True)
    server = models.IntegerField(choices=SERVER_CHOICES, default=SERVER_GLOBAL, null=True, blank=True)
    following = models.ManyToManyField("self", related_name='followed_by', symmetrical=False)
    public = models.BooleanField(default=False, blank=True)
    timezone = TimeZoneField(default='America/Los_Angeles')
    notes = models.TextField(null=True, blank=True)
    preferences = JSONField(default=dict)
    last_update = models.DateTimeField(auto_now=True)

    def get_rune_counts(self):
        counts = {}

        for rune_type in RuneInstance.TYPE_CHOICES:
            counts[rune_type[1]] = RuneInstance.objects.filter(owner=self, type=rune_type[0]).count()

        return counts

    def save(self, *args, **kwargs):
        super(Summoner, self).save(*args, **kwargs)

        # Update new storage model
        if not hasattr(self, 'storage'):
            new_storage = Storage.objects.create(
                owner=self,
            )
            new_storage.save()

    def __str__(self):
        return self.user.username


def _default_storage_data():
    return [0, 0, 0]


class Storage(models.Model):
    ESSENCE_LOW = 0
    ESSENCE_MID = 1
    ESSENCE_HIGH = 2

    ESSENCE_SIZES = [
        (ESSENCE_LOW, 'Low'),
        (ESSENCE_MID, 'Mid'),
        (ESSENCE_HIGH, 'High'),
    ]

    ESSENCE_FIELDS = ['magic_essence', 'fire_essence', 'water_essence', 'wind_essence', 'light_essence', 'dark_essence']
    CRAFT_FIELDS = [
        'wood',
        'leather',
        'rock',
        'ore',
        'mithril',
        'cloth',
        'rune_piece',
        'dust',
        'symbol_harmony',
        'symbol_transcendance',
        'symbol_chaos',
        'crystal_water',
        'crystal_fire',
        'crystal_wind',
        'crystal_light',
        'crystal_dark',
        'crystal_magic',
        'crystal_pure',
    ]
    MONSTER_FIELDS = [
        'fire_angelmon',
        'water_angelmon',
        'wind_angelmon',
        'light_angelmon',
        'dark_angelmon',
        'fire_king_angelmon',
        'water_king_angelmon',
        'wind_king_angelmon',
        'light_king_angelmon',
        'dark_king_angelmon',
        'rainbowmon_2_20',
        'rainbowmon_3_1',
        'rainbowmon_3_25',
        'rainbowmon_4_1',
        'rainbowmon_4_30',
        'rainbowmon_5_1',
        'super_angelmon',
        'devilmon',
    ]

    owner = models.OneToOneField(Summoner, on_delete=models.CASCADE)

    # Elemental Essences
    magic_essence = ArrayField(models.IntegerField(default=0), size=3, default=_default_storage_data, help_text='Magic Essence')
    fire_essence = ArrayField(models.IntegerField(default=0), size=3, default=_default_storage_data, help_text='Fire Essence')
    water_essence = ArrayField(models.IntegerField(default=0), size=3, default=_default_storage_data, help_text='Water Essence')
    wind_essence = ArrayField(models.IntegerField(default=0), size=3, default=_default_storage_data, help_text='Wind Essence')
    light_essence = ArrayField(models.IntegerField(default=0), size=3, default=_default_storage_data, help_text='Light Essence')
    dark_essence = ArrayField(models.IntegerField(default=0), size=3, default=_default_storage_data, help_text='Dark Essence')

    # Crafting materials
    wood = models.IntegerField(default=0, help_text='Hard Wood')
    leather = models.IntegerField(default=0, help_text='Tough Leather')
    rock = models.IntegerField(default=0, help_text='Solid Rock')
    ore = models.IntegerField(default=0, help_text='Solid Iron Ore')
    mithril = models.IntegerField(default=0, help_text='Shining Mythril')
    cloth = models.IntegerField(default=0, help_text='Thick Cloth')
    rune_piece = models.IntegerField(default=0, help_text='Rune Piece')
    dust = models.IntegerField(default=0, help_text='Magic Dust')
    symbol_harmony = models.IntegerField(default=0, help_text='Symbol of Harmony')
    symbol_transcendance = models.IntegerField(default=0, help_text='Symbol of Transcendance')
    symbol_chaos = models.IntegerField(default=0, help_text='Symbol of Chaos')
    crystal_water = models.IntegerField(default=0, help_text='Frozen Water Crystal')
    crystal_fire = models.IntegerField(default=0, help_text='Flaming Fire Crystal')
    crystal_wind = models.IntegerField(default=0, help_text='Whirling Wind Crystal')
    crystal_light = models.IntegerField(default=0, help_text='Shiny Light Crystal')
    crystal_dark = models.IntegerField(default=0, help_text='Pitch-black Dark Crystal')
    crystal_magic = models.IntegerField(default=0, help_text='Condensed Magic Crystal')
    crystal_pure = models.IntegerField(default=0, help_text='Pure Magic Crystal')

    # Material monsters
    fire_angelmon = models.IntegerField(default=0, help_text='Fire Angelmon')
    water_angelmon = models.IntegerField(default=0, help_text='Water Angelmon')
    wind_angelmon = models.IntegerField(default=0, help_text='Wind Angelmon')
    light_angelmon = models.IntegerField(default=0, help_text='Light Angelmon')
    dark_angelmon = models.IntegerField(default=0, help_text='Dark Angelmon')

    fire_king_angelmon = models.IntegerField(default=0, help_text='Fire King Angelmon')
    water_king_angelmon = models.IntegerField(default=0, help_text='Water King Angelmon')
    wind_king_angelmon = models.IntegerField(default=0, help_text='Wind King Angelmon')
    light_king_angelmon = models.IntegerField(default=0, help_text='Light King Angelmon')
    dark_king_angelmon = models.IntegerField(default=0, help_text='Dark King Angelmon')

    super_angelmon = models.IntegerField(default=0, help_text='Super Angelmon')
    devilmon = models.IntegerField(default=0, help_text='Devilmon')

    rainbowmon_2_20 = models.IntegerField(default=0, help_text='Rainbowmon 2⭐ lv.20')
    rainbowmon_3_1 = models.IntegerField(default=0, help_text='Rainbowmon 3⭐ lv.1')
    rainbowmon_3_25 = models.IntegerField(default=0, help_text='Rainbowmon 3⭐ lv.25')
    rainbowmon_4_1 = models.IntegerField(default=0, help_text='Rainbowmon 4⭐ lv.1')
    rainbowmon_4_30 = models.IntegerField(default=0, help_text='Rainbowmon 4⭐ lv.30')
    rainbowmon_5_1 = models.IntegerField(default=0, help_text='Rainbowmon 5⭐ lv.1')

    def get_storage(self):
        storage = OrderedDict()
        storage['magic'] = OrderedDict()
        storage['magic']['low'] = self.magic_essence[Storage.ESSENCE_LOW]
        storage['magic']['mid'] = self.magic_essence[Storage.ESSENCE_MID]
        storage['magic']['high'] = self.magic_essence[Storage.ESSENCE_HIGH]
        storage['fire'] = OrderedDict()
        storage['fire']['low'] = self.fire_essence[Storage.ESSENCE_LOW]
        storage['fire']['mid'] = self.fire_essence[Storage.ESSENCE_MID]
        storage['fire']['high'] = self.fire_essence[Storage.ESSENCE_HIGH]
        storage['water'] = OrderedDict()
        storage['water']['low'] = self.water_essence[Storage.ESSENCE_LOW]
        storage['water']['mid'] = self.water_essence[Storage.ESSENCE_MID]
        storage['water']['high'] = self.water_essence[Storage.ESSENCE_HIGH]
        storage['wind'] = OrderedDict()
        storage['wind']['low'] = self.wind_essence[Storage.ESSENCE_LOW]
        storage['wind']['mid'] = self.wind_essence[Storage.ESSENCE_MID]
        storage['wind']['high'] = self.wind_essence[Storage.ESSENCE_HIGH]
        storage['light'] = OrderedDict()
        storage['light']['low'] = self.light_essence[Storage.ESSENCE_LOW]
        storage['light']['mid'] = self.light_essence[Storage.ESSENCE_MID]
        storage['light']['high'] = self.light_essence[Storage.ESSENCE_HIGH]
        storage['dark'] = OrderedDict()
        storage['dark']['low'] = self.dark_essence[Storage.ESSENCE_LOW]
        storage['dark']['mid'] = self.dark_essence[Storage.ESSENCE_MID]
        storage['dark']['high'] = self.dark_essence[Storage.ESSENCE_HIGH]

        return storage

    @staticmethod
    def _min_zero(x):
        return max(x, 0)

    def save(self, *args, **kwargs):
        # Ensure all are at 0 or higher
        self.magic_essence = list(map(self._min_zero, self.magic_essence))
        self.fire_essence = list(map(self._min_zero, self.fire_essence))
        self.wind_essence = list(map(self._min_zero, self.wind_essence))
        self.light_essence = list(map(self._min_zero, self.light_essence))
        self.dark_essence = list(map(self._min_zero, self.dark_essence))

        self.wood = max(self.wood, 0)
        self.leather = max(self.leather, 0)
        self.rock = max(self.rock, 0)
        self.ore = max(self.ore, 0)
        self.mithril = max(self.mithril, 0)
        self.cloth = max(self.cloth, 0)
        self.rune_piece = max(self.rune_piece, 0)
        self.dust = max(self.dust, 0)
        self.symbol_harmony = max(self.symbol_harmony, 0)
        self.symbol_transcendance = max(self.symbol_transcendance, 0)
        self.symbol_chaos = max(self.symbol_chaos, 0)
        self.crystal_water = max(self.crystal_water, 0)
        self.crystal_fire = max(self.crystal_fire, 0)
        self.crystal_wind = max(self.crystal_wind, 0)
        self.crystal_light = max(self.crystal_light, 0)
        self.crystal_dark = max(self.crystal_dark, 0)
        self.crystal_magic = max(self.crystal_magic, 0)
        self.crystal_pure = max(self.crystal_pure, 0)

        super(Storage, self).save(*args, **kwargs)


class MonsterTag(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return mark_safe(self.name)


class MonsterInstance(models.Model, base.Stars):
    PRIORITY_DONE = 0
    PRIORITY_LOW = 1
    PRIORITY_MED = 2
    PRIORITY_HIGH = 3

    PRIORITY_CHOICES = [
        (PRIORITY_LOW, 'Low'),
        (PRIORITY_MED, 'Medium'),
        (PRIORITY_HIGH, 'High'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(Summoner, on_delete=models.CASCADE)
    monster = models.ForeignKey(Monster, on_delete=models.CASCADE)
    com2us_id = models.BigIntegerField(blank=True, null=True)
    created = models.DateTimeField(blank=True, null=True)
    stars = models.IntegerField(choices=base.Stars.STAR_CHOICES)
    level = models.IntegerField()
    skill_1_level = models.IntegerField(blank=True, default=1)
    skill_2_level = models.IntegerField(blank=True, default=1)
    skill_3_level = models.IntegerField(blank=True, default=1)
    skill_4_level = models.IntegerField(blank=True, default=1)
    fodder = models.BooleanField(default=False)
    in_storage = models.BooleanField(default=False)
    ignore_for_fusion = models.BooleanField(default=False)
    priority = models.IntegerField(choices=PRIORITY_CHOICES, blank=True, null=True)
    tags = models.ManyToManyField(MonsterTag, blank=True)
    notes = models.TextField(null=True, blank=True, help_text=mark_safe('<a href="https://daringfireball.net/projects/markdown/syntax" target="_blank">Markdown syntax</a> enabled'))
    custom_name = models.CharField(default='', max_length=20, blank=True)
    default_build = models.ForeignKey('RuneBuild', null=True, on_delete=models.SET_NULL, related_name='default_build')
    rta_build = models.ForeignKey('RuneBuild', null=True, on_delete=models.SET_NULL, related_name='rta_build')

    class Meta:
        ordering = ['-stars', '-level', 'monster__name']

    def __str__(self):
        return f'{self.get_stars_display()} {self.monster} Lv. {self.level}'

    def is_max_level(self):
        return self.level == self.monster.max_level_from_stars(self.stars)

    def max_level_from_stars(self):
        return self.monster.max_level_from_stars(self.stars)

    def skill_ups_to_max(self):
        skill_ups_remaining = self.monster.skill_ups_to_max or 0
        skill_levels = [self.skill_1_level, self.skill_2_level, self.skill_3_level, self.skill_4_level]

        for idx in range(0, self.monster.skills.count()):
            skill_ups_remaining -= skill_levels[idx] - 1

        return skill_ups_remaining

    # Stat values for current monster grade/level
    @cached_property
    def base_stats(self):
        return self.monster.get_stats(self.stars, self.level)

    @cached_property
    def max_base_stats(self):
        return self.monster.get_stats(6, 40)

    @property
    def base_hp(self):
        return self.base_stats[base.Stats.STAT_HP]

    @property
    def base_attack(self):
        return self.base_stats[base.Stats.STAT_ATK]

    @property
    def base_defense(self):
        return self.base_stats[base.Stats.STAT_DEF]

    @property
    def base_speed(self):
        return self.base_stats[base.Stats.STAT_SPD]

    @property
    def base_crit_rate(self):
        return self.base_stats[base.Stats.STAT_CRIT_RATE_PCT]

    @property
    def base_crit_damage(self):
        return self.base_stats[base.Stats.STAT_CRIT_DMG_PCT]

    @property
    def base_resistance(self):
        return self.base_stats[base.Stats.STAT_RESIST_PCT]

    @property
    def base_accuracy(self):
        return self.base_stats[base.Stats.STAT_ACCURACY_PCT]

    # Stat bonuses from default rune set
    @cached_property
    def rune_stats(self):
        return self._calc_rune_stats(self.base_stats.copy())

    @cached_property
    def max_rune_stats(self):
        return self._calc_rune_stats(self.max_base_stats.copy())

    def _calc_rune_stats(self, base_stats, rune_build=None):
        if rune_build is None:
            rune_stats = self.default_build.rune_stats.copy()
        else:
            rune_stats = rune_build.rune_stats.copy()

        # Convert HP/ATK/DEF percentage bonuses to flat bonuses based on the base stats
        for stat, converts_to in base.Stats.CONVERTS_TO_FLAT_STAT.items():
            rune_stats[converts_to] += int(ceil(round(base_stats.get(converts_to, 0.0) * (rune_stats[stat] / 100.0), 3)))
            del rune_stats[stat]

        return rune_stats

    @property
    def rune_hp(self):
        return self.rune_stats.get(base.Stats.STAT_HP, 0)

    @property
    def rune_attack(self):
        return self.rune_stats.get(base.Stats.STAT_ATK, 0)

    @property
    def rune_defense(self):
        return self.rune_stats.get(base.Stats.STAT_DEF, 0)

    @property
    def rune_speed(self):
        return self.rune_stats.get(base.Stats.STAT_SPD, 0)

    @property
    def rune_crit_rate(self):
        return self.rune_stats.get(base.Stats.STAT_CRIT_RATE_PCT, 0)

    @property
    def rune_crit_damage(self):
        return self.rune_stats.get(base.Stats.STAT_CRIT_DMG_PCT, 0)

    @property
    def rune_resistance(self):
        return self.rune_stats.get(base.Stats.STAT_RESIST_PCT, 0)

    @property
    def rune_accuracy(self):
        return self.rune_stats.get(base.Stats.STAT_ACCURACY_PCT, 0)

    # Totals for stats including rune bonuses
    def hp(self):
        return self.base_hp + self.rune_hp

    def attack(self):
        return self.base_attack + self.rune_attack

    def defense(self):
        return self.base_defense + self.rune_defense

    def speed(self):
        return self.base_speed + self.rune_speed

    def crit_rate(self):
        return self.base_crit_rate + self.rune_crit_rate

    def crit_damage(self):
        return self.base_crit_damage + self.rune_crit_damage

    def resistance(self):
        return self.base_resistance + self.rune_resistance

    def accuracy(self):
        return self.base_accuracy + self.rune_accuracy

    def get_max_level_stats(self):
        stats = {
            'base': {
                'hp': self.monster.actual_hp(6, 40),
                'attack': self.monster.actual_attack(6, 40),
                'defense': self.monster.actual_defense(6, 40),
            },
            'rune': {
                'hp': max_rune_stats.get(RuneInstance.STAT_HP, 0),
                'attack': max_rune_stats.get(RuneInstance.STAT_ATK, 0),
                'defense': max_rune_stats.get(RuneInstance.STAT_DEF, 0),
            },
        }

        stats['deltas'] = {
            'hp': int(round(float(stats['base']['hp'] + stats['rune']['hp']) / self.hp() * 100 - 100)),
            'attack': int(round(float(stats['base']['attack'] + stats['rune']['attack']) / self.attack() * 100 - 100)),
            'defense': int(round(float(stats['base']['defense'] + stats['rune']['defense']) / self.defense() * 100 - 100)),
        }

        return stats

    def get_building_stats(self, area=Building.AREA_GENERAL):
        owned_bldgs = BuildingInstance.objects.filter(
            Q(building__element__isnull=True) | Q(building__element=self.monster.element),
            owner=self.owner,
            building__area=area,
        ).select_related('building')

        bonuses = {
            Building.STAT_HP: 0,
            Building.STAT_ATK: 0,
            Building.STAT_DEF: 0,
            Building.STAT_SPD: 0,
            Building.STAT_CRIT_RATE_PCT: 0,
            Building.STAT_CRIT_DMG_PCT: 0,
            Building.STAT_RESIST_PCT: 0,
            Building.STAT_ACCURACY_PCT: 0,
        }

        for b in owned_bldgs:
            if b.building.affected_stat in bonuses.keys() and b.level > 0:
                bonuses[b.building.affected_stat] += b.building.stat_bonus[b.level - 1]

        return {
            'hp': int(ceil(round(self.base_hp * (bonuses[Building.STAT_HP] / 100.0), 3))),
            'attack': int(ceil(round(self.base_attack * (bonuses[Building.STAT_ATK] / 100.0), 3))),
            'defense': int(ceil(round(self.base_defense * (bonuses[Building.STAT_DEF] / 100.0), 3))),
            'speed': int(ceil(round(self.base_speed * (bonuses[Building.STAT_SPD] / 100.0), 3))),
            'crit_rate': bonuses[Building.STAT_CRIT_RATE_PCT],
            'crit_damage': bonuses[Building.STAT_CRIT_DMG_PCT],
            'resistance': bonuses[Building.STAT_RESIST_PCT],
            'accuracy': bonuses[Building.STAT_ACCURACY_PCT],
        }

    def get_guild_stats(self):
        return self.get_building_stats(Building.AREA_GUILD)

    def get_possible_skillups(self):
        same_family = Q(monster__family_id=self.monster.family_id)

        # Handle a few special cases for skillups outside of own family
        # Vampire Lord
        if self.monster.family_id == 23000:
            same_family |= Q(monster__family_id=14700)

        # Fairy Queen
        if self.monster.family_id == 19100:
            same_family |= Q(monster__family_id=10100)

        devilmon = MonsterInstance.objects.filter(owner=self.owner, monster__name='Devilmon').count()
        family = MonsterInstance.objects.filter(owner=self.owner).filter(same_family).exclude(pk=self.pk).order_by('ignore_for_fusion')
        pieces = MonsterPiece.objects.filter(owner=self.owner, monster__family_id=self.monster.family_id)

        return {
            'devilmon': devilmon,
            'family': family,
            'pieces': pieces,
            'none': devilmon + family.count() + pieces.count() == 0,
        }

    def clean(self):
        from django.core.exceptions import ValidationError

        # Remove custom name if not a homunculus
        if not self.monster.homunculus:
            self.custom_name = ''

        # Check skill levels
        max_levels = self.monster.skills.all().values_list('max_level', flat=True)
        if self.skill_1_level is None or self.skill_1_level < 1:
            self.skill_1_level = 1
        if len(max_levels) >= 1 and self.skill_1_level > max_levels[0]:
            self.skill_1_level = max_levels[0]

        if self.skill_2_level is None or self.skill_2_level < 1:
            self.skill_2_level = 1
        if len(max_levels) >= 2 and self.skill_2_level > max_levels[1]:
            self.skill_1_level = max_levels[1]

        if self.skill_3_level is None or self.skill_3_level < 1:
            self.skill_3_level = 1
        if len(max_levels) >= 3 and self.skill_3_level > max_levels[2]:
            self.skill_1_level = max_levels[2]

        if self.skill_4_level is None or self.skill_4_level < 1:
            self.skill_4_level = 1
        if len(max_levels) >= 4 and self.skill_4_level > max_levels[3]:
            self.skill_1_level = max_levels[3]

        if self.level > 40 or self.level < 1:
            raise ValidationError(
                'Level out of range (Valid range %(min)s-%(max)s)',
                params={'min': 1, 'max': 40},
                code='invalid_level'
            )

        if self.stars and (self.level > 10 + self.stars * 5):
            raise ValidationError(
                'Level exceeds max for given star rating (Max: %(value)s)',
                params={'value': 10 + self.stars * 5},
                code='invalid_level'
            )

        min_stars = self.monster.base_monster.base_stars

        if self.stars and (self.stars > 6 or self.stars < min_stars):
            raise ValidationError(
                'Star rating out of range (%(min)s to %(max)s)',
                params={'min': min_stars, 'max': 6},
                code='invalid_stars'
            )

        super(MonsterInstance, self).clean()

    def save(self, *args, **kwargs):
        super(MonsterInstance, self).save(*args, **kwargs)

        if self.default_build is None or self.rta_build is None:
            self._initialize_rune_build()

    def _initialize_rune_build(self):
        # Create empty rune builds if none exists
        added = False
        if self.default_build is None:
            self.default_build = RuneBuild.objects.create(
                owner_id=self.owner.pk,
                monster_id=self.pk,
                name='Equipped Runes',
            )

        if self.rta_build is None:
            self.rta_build = RuneBuild.objects.create(
                owner_id=self.owner.pk,
                monster_id=self.pk,
                name='Real-Time Arena',
            )
            added = True

        if added:
            self.save()

        self.default_build.runes.set(self.runeinstance_set.all())


class MonsterPiece(models.Model):
    PIECE_REQUIREMENTS = {
        1: 10,
        2: 20,
        3: 40,
        4: 50,
        5: 100,
    }

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(Summoner, on_delete=models.CASCADE)
    monster = models.ForeignKey(Monster, on_delete=models.CASCADE)
    pieces = models.IntegerField(default=0)

    class Meta:
        ordering = ['monster__name']

    def __str__(self):
        return str(self.monster) + ' - ' + str(self.pieces) + ' pieces'

    def can_summon(self):
        return int(floor(self.pieces / self.PIECE_REQUIREMENTS[self.monster.natural_stars]))


class RuneInstance(Rune):
    # Upgrade success rate based on rune level
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.IntegerField(choices=Rune.TYPE_CHOICES)
    owner = models.ForeignKey(Summoner, on_delete=models.CASCADE)
    com2us_id = models.BigIntegerField(blank=True, null=True)
    assigned_to = models.ForeignKey(MonsterInstance, on_delete=models.SET_NULL, blank=True, null=True)
    marked_for_sale = models.BooleanField(default=False)
    notes = models.TextField(null=True, blank=True)

    __original_assigned_to_id = None

    # Old substat fields to be removed later, but still used
    substat_1 = models.IntegerField(choices=Rune.STAT_CHOICES, null=True, blank=True)
    substat_1_value = models.IntegerField(null=True, blank=True)
    substat_1_craft = models.IntegerField(choices=RuneCraft.CRAFT_CHOICES, null=True, blank=True)
    substat_2 = models.IntegerField(choices=Rune.STAT_CHOICES, null=True, blank=True)
    substat_2_value = models.IntegerField(null=True, blank=True)
    substat_2_craft = models.IntegerField(choices=RuneCraft.CRAFT_CHOICES, null=True, blank=True)
    substat_3 = models.IntegerField(choices=Rune.STAT_CHOICES, null=True, blank=True)
    substat_3_value = models.IntegerField(null=True, blank=True)
    substat_3_craft = models.IntegerField(choices=RuneCraft.CRAFT_CHOICES, null=True, blank=True)
    substat_4 = models.IntegerField(choices=Rune.STAT_CHOICES, null=True, blank=True)
    substat_4_value = models.IntegerField(null=True, blank=True)
    substat_4_craft = models.IntegerField(choices=RuneCraft.CRAFT_CHOICES, null=True, blank=True)

    class Meta:
        ordering = ['slot', 'type', 'level']

    def __init__(self, *args, **kwargs):
        super(RuneInstance, self).__init__(*args, **kwargs)
        self.__original_assigned_to_id = self.assigned_to_id

    def clean(self):
        super().clean()

        if self.assigned_to is not None and (self.assigned_to.runeinstance_set.filter(slot=self.slot).exclude(pk=self.pk).count() > 0):
            raise ValidationError(
                'Monster already has rune in slot %(slot)s.',
                params={
                    'slot': self.slot,
                },
                code='slot_occupied'
            )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.assigned_to:
            # Check no other runes are in this slot
            for rune in RuneInstance.objects.filter(assigned_to=self.assigned_to, slot=self.slot).exclude(pk=self.pk):
                rune.assigned_to = None
                rune.save()

            # Trigger stat calc update on the assigned monster
            self.assigned_to.save()

            # Update default rune build on that monster
            # TODO: Remove this once rune builds are default method of working with equipped runes
            self.assigned_to._initialize_rune_build()
        else:
            # TODO: Remove this once rune builds are default method of working with equipped runes
            if self.__original_assigned_to_id is not None and self.assigned_to is None:
                # Rune was removed, update rune build on that monster
                MonsterInstance.objects.get(pk=self.__original_assigned_to_id)._initialize_rune_build()


class RuneBuild(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(Summoner, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, default='')
    runes = models.ManyToManyField(RuneInstance)
    avg_efficiency = models.FloatField(default=0)
    monster = models.ForeignKey(MonsterInstance, on_delete=models.CASCADE)

    # Stat bonuses
    hp = models.IntegerField(default=0)
    hp_pct = models.IntegerField(default=0)
    attack = models.IntegerField(default=0)
    attack_pct = models.IntegerField(default=0)
    defense = models.IntegerField(default=0)
    defense_pct = models.IntegerField(default=0)
    speed = models.IntegerField(default=0)
    crit_rate = models.IntegerField(default=0)
    crit_damage = models.IntegerField(default=0)
    resistance = models.IntegerField(default=0)
    accuracy = models.IntegerField(default=0)

    # TODO: Tagging

    def __str__(self):
        return f'{self.name} - {self.rune_set_summary}'
        # return f'{self.name}'

    @cached_property
    def rune_set_summary(self):
        num_equipped = self.runes.count()

        if not num_equipped:
            return 'Empty'

        # Build list of set names
        active_set_names = [
            RuneInstance.TYPE_CHOICES[rune_type - 1][1] for rune_type in self.active_rune_sets
        ]

        # Check if broken set present
        active_set_required_count = sum([
            RuneInstance.RUNE_SET_BONUSES[rune_set]['count'] for rune_set in self.active_rune_sets
        ])

        if num_equipped > active_set_required_count:
            active_set_names.append('Broken')

        set_summary = '/'.join(active_set_names)

        # Build main stat list for even slots
        main_stat_summary = '/'.join([
            rune.get_main_stat_display() for rune in self.runes.filter(slot__in=[2, 4, 6])
        ])

        return f'{set_summary} - {main_stat_summary}'

    @cached_property
    def rune_set_bonus_text(self):
        return [
            f'{RuneInstance.RUNE_SET_BONUSES[active_set]["description"]}' for active_set in self.active_rune_sets
        ]

    @cached_property
    def active_rune_sets(self):
        completed_sets = []

        for set_counts in self.runes.values('type').order_by().annotate(count=Count('type')):
            required = RuneInstance.RUNE_SET_COUNT_REQUIREMENTS[set_counts['type']]
            present = set_counts['count']
            completed_sets.extend([set_counts['type']] * (present // required))

        return completed_sets

    @cached_property
    def rune_stats(self):
        stats = {
            base.Stats.STAT_HP: self.hp,
            base.Stats.STAT_HP_PCT: self.hp_pct,
            base.Stats.STAT_ATK: self.attack,
            base.Stats.STAT_ATK_PCT: self.attack_pct,
            base.Stats.STAT_DEF: self.defense,
            base.Stats.STAT_DEF_PCT: self.defense_pct,
            base.Stats.STAT_SPD: self.speed,
            base.Stats.STAT_CRIT_RATE_PCT: self.crit_rate,
            base.Stats.STAT_CRIT_DMG_PCT: self.crit_damage,
            base.Stats.STAT_RESIST_PCT: self.resistance,
            base.Stats.STAT_ACCURACY_PCT: self.accuracy,
        }

        return stats

    def update_stats(self):
        # Sum all stats on the runes
        stat_bonuses = {}
        runes = self.runes.all()
        for stat, _ in RuneInstance.STAT_CHOICES:
            if stat not in stat_bonuses:
                stat_bonuses[stat] = 0

            for rune in runes:
                stat_bonuses[stat] += rune.get_stat(stat)

        # Add in any active set bonuses
        for active_set in self.active_rune_sets:
            stat = RuneInstance.RUNE_SET_BONUSES[active_set]['stat']
            if stat:
                stat_bonuses[stat] += RuneInstance.RUNE_SET_BONUSES[active_set]['value']

        self.hp = stat_bonuses.get(base.Stats.STAT_HP, 0)
        self.hp_pct = stat_bonuses.get(base.Stats.STAT_HP_PCT, 0)
        self.attack = stat_bonuses.get(base.Stats.STAT_ATK, 0)
        self.attack_pct = stat_bonuses.get(base.Stats.STAT_ATK_PCT, 0)
        self.defense = stat_bonuses.get(base.Stats.STAT_DEF, 0)
        self.defense_pct = stat_bonuses.get(base.Stats.STAT_DEF_PCT, 0)
        self.speed = stat_bonuses.get(base.Stats.STAT_SPD, 0)
        self.crit_rate = stat_bonuses.get(base.Stats.STAT_CRIT_RATE_PCT, 0)
        self.crit_damage = stat_bonuses.get(base.Stats.STAT_CRIT_DMG_PCT, 0)
        self.resistance = stat_bonuses.get(base.Stats.STAT_RESIST_PCT, 0)
        self.accuracy = stat_bonuses.get(base.Stats.STAT_ACCURACY_PCT, 0)
        self.avg_efficiency = self.runes.aggregate(Avg('efficiency'))['efficiency__avg'] or 0.0


class RuneCraftInstance(RuneCraft):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(Summoner, on_delete=models.CASCADE)
    com2us_id = models.BigIntegerField(blank=True, null=True)
    quantity = models.IntegerField(default=1)

    class Meta:
        ordering = ['type', 'rune']

    def clean(self):
        if self.quantity < 1:
            raise ValidationError({'quantity': ValidationError(
                'Quantity must be 1 or more',
                code='invalid_quantity'
            )})


class TeamGroup(models.Model):
    owner = models.ForeignKey(Summoner, on_delete=models.CASCADE)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=30)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Team(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(Summoner, on_delete=models.CASCADE, null=True, blank=True)
    level = models.ForeignKey(Level, on_delete=models.SET_NULL, null=True, blank=True)
    group = models.ForeignKey(TeamGroup, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=30)
    favorite = models.BooleanField(default=False, blank=True)
    description = models.TextField(
        null=True,
        blank=True,
        help_text=mark_safe('<a href="https://daringfireball.net/projects/markdown/syntax" target="_blank">Markdown syntax</a> enabled')
    )
    leader = models.ForeignKey('MonsterInstance', on_delete=models.SET_NULL, related_name='team_leader', null=True, blank=True)
    roster = models.ManyToManyField('MonsterInstance', blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class BuildingInstance(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(Summoner, on_delete=models.CASCADE)
    building = models.ForeignKey(Building, on_delete=models.CASCADE)
    level = models.IntegerField()

    class Meta:
        ordering = ['building']

    def remaining_upgrade_cost(self):
        return sum(self.building.upgrade_cost[self.level:])

    def __str__(self):
        return str(self.building) + ', Lv.' + str(self.level)

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.level and self.building and (self.level < 0 or self.level > self.building.max_level):
            raise ValidationError({
                    'level': ValidationError(
                        'Level must be between %s and %s' % (0, self.building.max_level),
                        code='invalid_level',
                    )
                })

    def update_fields(self):
        self.level = min(max(0, self.level), self.building.max_level)

    def save(self, *args, **kwargs):
        self.update_fields()
        super(BuildingInstance, self).save(*args, **kwargs)
