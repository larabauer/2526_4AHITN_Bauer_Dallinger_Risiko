import random

from map_data import MapData


class GameInitializer:

    @staticmethod
    def distribute_countries(num_players: int) -> list[list[str]]:
        countries = MapData.get_country_names()
        random.shuffle(countries)

        allocations = GameInitializer._compute_allocations(num_players, len(countries))

        result = []
        index = 0
        for count in allocations:
            result.append(countries[index : index + count])
            index += count

        return result

    @staticmethod
    def _compute_allocations(num_players: int, num_countries: int) -> list[int]:
        base = num_countries // num_players
        remainder = num_countries % num_players
        return [base + (1 if i < remainder else 0) for i in range(num_players)]