from rest_framework import serializers

from bestiary import models


class CraftMaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CraftMaterial
        fields = ['id', 'url', 'name', 'icon_filename']
        extra_kwargs = {
            'url': {
                'view_name': 'bestiary/craft-materials-detail',
            },
        }


class SourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Source
        fields = ['id', 'url', 'name', 'description', 'farmable_source']
        extra_kwargs = {
            'url': {
                'view_name': 'bestiary/monster-sources-detail',
            },
        }


class SkillEffectSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SkillEffect
        fields = ('id', 'url', 'name', 'is_buff', 'description', 'icon_filename')
        extra_kwargs = {
            'url': {
                'view_name': 'bestiary/skill-effects-detail',
            },
        }


class SkillEffectDetailSerializer(serializers.ModelSerializer):
    effect = SkillEffectSerializer()

    class Meta:
        model = models.SkillEffectDetail
        fields = [
            'effect',
            'aoe', 'single_target', 'self_effect',
            'chance', 'on_crit', 'on_death', 'random',
            'quantity', 'all', 'self_hp', 'target_hp', 'damage',
            'note',
        ]


class SkillSerializer(serializers.HyperlinkedModelSerializer):
    level_progress_description = serializers.SerializerMethodField()
    effects = SkillEffectDetailSerializer(many=True, read_only=True, source='skilleffectdetail_set')
    scales_with = serializers.SerializerMethodField()
    used_on = serializers.PrimaryKeyRelatedField(source='monster_set', many=True, read_only=True)

    class Meta:
        model = models.Skill
        fields = (
            'id', 'com2us_id', 'name', 'description', 'slot', 'cooltime', 'hits', 'passive', 'aoe',
            'max_level', 'level_progress_description', 'effects', 'multiplier_formula', 'multiplier_formula_raw',
            'scales_with', 'icon_filename', 'used_on',
        )

    def get_level_progress_description(self, instance):
        if instance.level_progress_description:
            return instance.level_progress_description.rstrip().split('\n')
        else:
            return []

    def get_scales_with(self, instance):
        return instance.scaling_stats.values_list('stat', flat=True)


class LeaderSkillSerializer(serializers.ModelSerializer):
    attribute = serializers.SerializerMethodField('get_stat')
    area = serializers.SerializerMethodField()
    element = serializers.SerializerMethodField()

    class Meta:
        model = models.LeaderSkill
        fields = ('id', 'url', 'attribute', 'amount', 'area', 'element')
        extra_kwargs = {
            'url': {
                'view_name': 'bestiary/leader-skills-detail',
            },
        }

    def get_stat(self, instance):
        return instance.get_attribute_display()

    def get_area(self, instance):
        return instance.get_area_display()

    def get_element(self, instance):
        return instance.get_element_display()


class HomunculusSkillCraftCostSerializer(serializers.ModelSerializer):
    material = CraftMaterialSerializer(source='craft', read_only=True)

    class Meta:
        model = models.HomunculusSkillCraftCost
        fields = ['material', 'quantity']


class HomunculusSkillSerializer(serializers.ModelSerializer):
    craft_materials = HomunculusSkillCraftCostSerializer(source='homunculusskillcraftcost_set', many=True, read_only=True)
    used_on = serializers.PrimaryKeyRelatedField(source='monsters', many=True, read_only=True)

    class Meta:
        model = models.HomunculusSkill
        fields = ['id', 'url', 'skill', 'craft_materials', 'mana_cost', 'prerequisites', 'used_on']
        extra_kwargs = {
            'url': {
                'view_name': 'bestiary/homunculus-skills-detail',
            },
        }


class MonsterCraftCostSerializer(serializers.ModelSerializer):
    material = CraftMaterialSerializer(source='craft', read_only=True)

    class Meta:
        model = models.MonsterCraftCost
        fields = ['material', 'quantity']


class MonsterSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='bestiary/monsters-detail')
    element = serializers.SerializerMethodField()
    archetype = serializers.SerializerMethodField()
    source = SourceSerializer(many=True, read_only=True)
    leader_skill = LeaderSkillSerializer(read_only=True)
    homunculus_skills = serializers.PrimaryKeyRelatedField(source='homunculusskill_set', read_only=True, many=True)
    craft_materials = MonsterCraftCostSerializer(many=True, source='monstercraftcost_set', read_only=True)

    class Meta:
        model = models.Monster
        fields = (
            'id', 'url', 'com2us_id', 'family_id',
            'name', 'image_filename', 'element', 'archetype', 'base_stars', 'natural_stars',
            'obtainable', 'can_awaken', 'awaken_level', 'awaken_bonus',
            'skills', 'skill_ups_to_max', 'leader_skill', 'homunculus_skills',
            'base_hp', 'base_attack', 'base_defense', 'speed', 'crit_rate', 'crit_damage', 'resistance', 'accuracy',
            'raw_hp', 'raw_attack', 'raw_defense', 'max_lvl_hp', 'max_lvl_attack', 'max_lvl_defense',
            'awakens_from', 'awakens_to',
            'awaken_mats_fire_low', 'awaken_mats_fire_mid', 'awaken_mats_fire_high',
            'awaken_mats_water_low', 'awaken_mats_water_mid', 'awaken_mats_water_high',
            'awaken_mats_wind_low', 'awaken_mats_wind_mid', 'awaken_mats_wind_high',
            'awaken_mats_light_low', 'awaken_mats_light_mid', 'awaken_mats_light_high',
            'awaken_mats_dark_low', 'awaken_mats_dark_mid', 'awaken_mats_dark_high',
            'awaken_mats_magic_low', 'awaken_mats_magic_mid', 'awaken_mats_magic_high',
            'source', 'fusion_food',
            'homunculus', 'craft_cost', 'craft_materials',
        )

    def get_element(self, instance):
        return instance.get_element_display()

    def get_archetype(self, instance):
        return instance.get_archetype_display()


class FusionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Fusion
        fields = ['id', 'url', 'product', 'cost', 'ingredients']
        extra_kwargs = {
            'url': {
                'view_name': 'bestiary/fusions-detail',
            },
        }


class BuildingSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='bestiary/buildings-detail')
    area = serializers.SerializerMethodField()
    affected_stat = serializers.SerializerMethodField()
    element = serializers.SerializerMethodField()

    class Meta:
        model = models.Building
        fields = [
            'id',
            'url',
            'area',
            'affected_stat',
            'element',
            'com2us_id',
            'name',
            'max_level',
            'stat_bonus',
            'upgrade_cost',
            'description',
            'icon_filename',
        ]

    def get_area(self, instance):
        return instance.get_area_display()

    def get_affected_stat(self, instance):
        return instance.get_affected_stat_display()

    def get_element(self, instance):
        return instance.get_element_display()


class DungeonSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='bestiary/dungeons-detail')
    levels = serializers.PrimaryKeyRelatedField(source='level_set', read_only=True, many=True)
    category = serializers.SerializerMethodField()

    class Meta:
        model = models.Dungeon
        fields = [
            'id',
            'url',
            'enabled',
            'name',
            'slug',
            'category',
            'icon',
            'levels',
        ]

    def get_category(self, instance):
        return instance.get_category_display()


class LevelSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='bestiary/levels-detail')
    difficulty = serializers.SerializerMethodField()

    class Meta:
        model = models.Level
        fields = [
            'id',
            'url',
            'dungeon',
            'floor',
            'difficulty',
            'energy_cost',
            'xp',
            'frontline_slots',
            'backline_slots',
            'total_slots',
        ]

    def get_difficulty(self, instance):
        return instance.get_difficulty_display()
