from map_data import MapData


class Player:
    def __init__(self, name: str, color: tuple[int, int, int]):
        self.name = name
        self.color = color
        self.territories: list = []
        self.reinforcements: int = 0

    def add_territory(self, territory) -> None:
        self.territories.append(territory)

    def remove_territory(self, territory) -> None:
        if territory in self.territories:
            self.territories.remove(territory)
            territory.owner = None

    def calculate_reinforcements(self) -> None:
        territory_bonus = max(3, len(self.territories) // 3)
        territory_names = [t.name for t in self.territories]
        continent_bonus = MapData.calculate_continent_bonus(territory_names)
        self.reinforcements = territory_bonus + continent_bonus

    def __str__(self) -> str:
        return f"Player: {self.name} {self.color}"

    def __repr__(self) -> str:
        return self.__str__()