from rest_framework import serializers

from bestiary import models


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


class EnemySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Enemy
        fields = [
            'id',
            'monster',
            'stars',
            'level',
            'hp',
            'attack',
            'defense',
            'speed',
            'resist',
            'crit_bonus',
            'crit_damage_reduction',
            'accuracy_bonus',
        ]


class WaveSerializer(serializers.ModelSerializer):
    enemies = EnemySerializer(source='enemy_set', many=True, read_only=True)

    class Meta:
        model = models.Wave
        fields = [
            'enemies',
        ]


class LevelSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='bestiary/levels-detail')
    difficulty = serializers.SerializerMethodField()
    waves = WaveSerializer(source='wave_set', many=True, read_only=True)

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
            'waves',
        ]

    def get_difficulty(self, instance):
        return instance.get_difficulty_display()
