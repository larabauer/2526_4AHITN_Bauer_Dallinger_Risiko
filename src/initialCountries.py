import json
import random


def get_countries_from_json():
    with open("resources/continents.json", "r", encoding="utf-8") as file:
        data = json.load(file)

    countries = [
        country
        for continent in data
        for key, value in continent.items()
        if key != "points"
        for country in value
    ]

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