from rest_framework import serializers

from bestiary import models


class GameItemSerializer(serializers.ModelSerializer):
    category = serializers.SerializerMethodField()

    class Meta:
        model = models.GameItem
        fields = [
            'id',
            'com2us_id',
            'url',
            'name',
            'category',
            'icon',
            'description',
            'sell_value',
        ]
        extra_kwargs = {
            'url': {
                'view_name': 'bestiary/items-detail',
            },
        }

    def get_category(self, instance):
        return instance.get_category_display()


class SourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Source
        fields = ['id', 'url', 'name', 'description', 'farmable_source']
        extra_kwargs = {
            'url': {
                'view_name': 'bestiary/monster-sources-detail',
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
