import json
import random



def get_countries_from_json():
    with open("resources/countries.json", "r", encoding="utf-8") as file:
        data = json.load(file)
    return data

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
    num_countries = len(countries)
    random.shuffle(countries)

    player_nums = initial_num_countries_for_players(players, num_countries)

    result = []
    index = 0

    for num in player_nums:
        player_countries = countries[index:index + num]
        result.append(player_countries)
        index += num

    return result