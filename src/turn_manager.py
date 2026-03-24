class TurnManager:
    def __init__(self, players):
        self.players = players
        self.current_index = 0

        # Phasen: placement → attack → move (später erweiterbar)
        self.phase = "placement"

    def get_current_player(self):
        return self.players[self.current_index]

    def next_player(self):
        self.current_index = (self.current_index + 1) % len(self.players)
        self.phase = "placement"  # neuer Spieler startet wieder mit Placement

    def set_phase(self, phase):
        self.phase = phase

    def is_current_player(self, player):
        return player == self.get_current_player()

    def __str__(self):
        p = self.get_current_player()
        return f"Turn: {p.name} | Phase: {self.phase}"