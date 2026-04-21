from initialCountries import calculate_continent_bonus

class Player:
    def __init__(self, name, color):
        self.name = name
        self.color = color

        # wie viele Truppen erhält der spieler zum setzen?
        self.reinforcements = 0

        # Truppen für eroberte Kontinente
        self.additional_forces = 0

        self.territories = []

    def add_territory(self, territory):
        self.territories.append(territory)


    def remove_territory(self, territory):
        if territory in self.territories:
            self.territories.remove(territory)
            territory.owner = None

    def calculate_reinforcements(self, map_data):
        territory_bonus = max(3, len(self.territories) // 3)
        continent_bonus = 0

        player_territory_names = [t.name for t in self.territories]

        for continent in map_data["continents"]:
            continent_name = continent["name"]
            continent_points = continent["points"]

            continent_countries = [
                country["name"]
                for country in map_data["countries"]
                if country["continent"] == continent_name
            ]

            if all(country_name in player_territory_names for country_name in continent_countries):
                continent_bonus += continent_points

        self.reinforcements = territory_bonus + continent_bonus

    def __str__(self):
        return "Player: " + self.name + " " + str(self.color)

    def __repr__(self): # for toString bei Liste
        return self.__str__()