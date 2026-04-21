import json
import random


def load_map_data():
    with open("resources/continents.json", "r", encoding="utf-8") as file:
        return json.load(file)


def get_countries_from_json():
    data = load_map_data()
    countries = [country["name"] for country in data["countries"]]
    print("Länder geladen:", countries)
    return countries


def initial_num_countries_for_players(players: int, num_countries: int):
    base = num_countries // players
    remainder = num_countries % players

    result = []
    for i in range(players):
        if i < remainder:
            result.append(base + 1)
        else:
            result.append(base)

    return result


def calculate_continent_bonus(player, map_data):
    bonus = 0
    player_territory_names = [t.name for t in player.territories]

    for continent in map_data["continents"]:
        continent_name = continent["name"]
        continent_points = continent["points"]

        continent_countries = [
            country["name"]
            for country in map_data["countries"]
            if country["continent"] == continent_name
        ]

        if all(country_name in player_territory_names for country_name in continent_countries):
            bonus += continent_points

    return bonus


def initial_countries_for_players(players: int):
    countries = get_countries_from_json()
    random.shuffle(countries)

    player_nums = initial_num_countries_for_players(players, len(countries))

    result = []
    index = 0

    for num in player_nums:
        player_countries = countries[index:index + num]
        result.append(player_countries)
        index += num

    return result