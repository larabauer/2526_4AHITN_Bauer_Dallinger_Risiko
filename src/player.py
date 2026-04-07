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

    def calculate_reinforcements(self):
        self.reinforcements = max(3, len(self.territories) // 3) + self.additional_forces

    def __str__(self):
        return "Player: " + self.name + " " + str(self.color)

    def __repr__(self): # for toString bei Liste
        return self.__str__()