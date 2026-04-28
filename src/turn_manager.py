class TurnManager:
    PHASES = ("placement", "attack", "move")

    def __init__(self, players: list):
        self.players = players
        self.current_index: int = 0
        self.phase: str = "placement"

    def get_current_player(self):
        return self.players[self.current_index]

    def next_player(self) -> None:
        self.current_index = (self.current_index + 1) % len(self.players)
        self.phase = "placement"

    def set_phase(self, phase: str) -> None:
        if phase not in self.PHASES:
            raise ValueError(f"Ungültige Phase '{phase}'. Erlaubt: {self.PHASES}")
        self.phase = phase

    def is_current_player(self, player) -> bool:
        return player == self.get_current_player()

    def __str__(self) -> str:
        p = self.get_current_player()
        return f"Turn: {p.name} | Phase: {self.phase}"