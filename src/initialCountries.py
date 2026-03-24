import json
import random

NUM_COUNTRIES = 42

def get_countries_from_json():
    with open("resources/countries.json", "r", encoding="utf-8") as file:
        data = json.load(file)
    return data

def initial_num_countries_for_players(players: int):
    base = NUM_COUNTRIES // players
    remainder = NUM_COUNTRIES % players

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

    player_nums = initial_num_countries_for_players(players)

    result = []
    index = 0

    for num in player_nums:
        player_countries = countries[index:index + num]
        result.append(player_countries)
        index += num

    return result