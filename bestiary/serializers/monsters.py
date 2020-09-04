from rest_framework import serializers

from bestiary import models

from .items import GameItemSerializer, SourceSerializer
from .skills import LeaderSkillSerializer


class MonsterCraftCostSerializer(serializers.ModelSerializer):
    item = GameItemSerializer(read_only=True)

    class Meta:
        model = models.MonsterCraftCost
        fields = ['item', 'quantity']


class AwakenCostSerializer(serializers.ModelSerializer):
    item = GameItemSerializer(read_only=True)

    class Meta:
        model = models.AwakenCost
        fields = ['item', 'quantity']


class MonsterSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='bestiary/monsters-detail')
    element = serializers.SerializerMethodField()
    archetype = serializers.SerializerMethodField()
    source = SourceSerializer(many=True, read_only=True)
    leader_skill = LeaderSkillSerializer(read_only=True)
    awaken_cost = AwakenCostSerializer(source='awakencost_set', many=True, read_only=True)
    homunculus_skills = serializers.PrimaryKeyRelatedField(source='homunculusskill_set', read_only=True, many=True)
    craft_materials = MonsterCraftCostSerializer(many=True, source='monstercraftcost_set', read_only=True)

    class Meta:
        model = models.Monster
        fields = (
            'id', 'url', 'bestiary_slug', 'com2us_id', 'family_id',
            'name', 'image_filename', 'element', 'archetype', 'base_stars', 'natural_stars',
            'obtainable', 'can_awaken', 'awaken_level', 'awaken_bonus',
            'skills', 'skill_ups_to_max', 'leader_skill', 'homunculus_skills',
            'base_hp', 'base_attack', 'base_defense', 'speed', 'crit_rate', 'crit_damage', 'resistance', 'accuracy',
            'raw_hp', 'raw_attack', 'raw_defense', 'max_lvl_hp', 'max_lvl_attack', 'max_lvl_defense',
            'awakens_from', 'awakens_to', 'awaken_cost',
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
