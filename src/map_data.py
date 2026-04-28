import json


class MapData:
    _data: dict | None = None

    @classmethod #static
    def load(cls) -> dict:
        if cls._data is None:
            with open("resources/continents.json", "r", encoding="utf-8") as f:
                cls._data = json.load(f)
        return cls._data

    @classmethod
    def get_country_names(cls) -> list[str]:
        return [country["name"] for country in cls.load()["countries"]]

    @classmethod
    def get_country_neighbours(cls, country_name):
        for country in cls.load()["countries"]:
            if country["name"] == country_name:
                return country["neighbors"]

        return []

    @classmethod
    def calculate_continent_bonus(cls, player_territory_names: list[str]) -> int:
        data = cls.load()
        bonus = 0

        for continent in data["continents"]:
            continent_countries = [
                c["name"]
                for c in data["countries"]
                if c["continent"] == continent["name"]
            ]
            if all(name in player_territory_names for name in continent_countries):
                bonus += continent["points"]

        return bonus