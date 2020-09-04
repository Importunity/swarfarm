from rest_framework import serializers

from bestiary import models
from .items import GameItemSerializer


class SkillUpgradeSerializer(serializers.ModelSerializer):
    effect = serializers.SerializerMethodField()

    class Meta:
        model = models.SkillUpgrade
        fields = ('effect', 'amount')

    def get_effect(self, instance):
        return instance.get_effect_display()


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
    upgrades = SkillUpgradeSerializer(many=True, read_only=True)
    effects = SkillEffectDetailSerializer(many=True, read_only=True, source='skilleffectdetail_set')
    scales_with = serializers.SerializerMethodField()
    used_on = serializers.PrimaryKeyRelatedField(source='monster_set', many=True, read_only=True)

    class Meta:
        model = models.Skill
        fields = (
            'id', 'com2us_id', 'name', 'description', 'slot', 'cooltime', 'hits', 'passive', 'aoe',
            'max_level', 'upgrades', 'effects', 'multiplier_formula', 'multiplier_formula_raw',
            'scales_with', 'icon_filename', 'used_on', 'level_progress_description',
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
    item = GameItemSerializer(read_only=True)

    class Meta:
        model = models.HomunculusSkillCraftCost
        fields = ['item', 'quantity']


class HomunculusSkillSerializer(serializers.ModelSerializer):
    craft_materials = HomunculusSkillCraftCostSerializer(source='homunculusskillcraftcost_set', many=True, read_only=True)
    used_on = serializers.PrimaryKeyRelatedField(source='monsters', many=True, read_only=True)

    class Meta:
        model = models.HomunculusSkill
        fields = ['id', 'url', 'skill', 'craft_materials', 'prerequisites', 'used_on']
        extra_kwargs = {
            'url': {
                'view_name': 'bestiary/homunculus-skills-detail',
            },
        }
