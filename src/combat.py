import random


class Combat:
    MAX_ATTACKER_DICE = 3
    MAX_DEFENDER_DICE = 2

    def __init__(self, attacking_territory, defending_territory, players: list):
        self.attacking_territory = attacking_territory
        self.defending_territory = defending_territory
        self.players = players

        self.attacker = players[attacking_territory.owner]
        self.defender = players[defending_territory.owner]

        self.attacker_dice: list[int] = []
        self.defender_dice: list[int] = []
        self.last_attacker_losses = 0
        self.last_defender_losses = 0

        self.attacker_dice_num = 0
        self.defender_dice_num = 0

    def fight(self, num_dice_attacker):
        self.roll_attacker(num_dice_attacker)
        self.roll_defender()
        self.resolve_combat()
        if self.check_conquest():
            self.conquer(self.attacker_dice_num)

    def roll_dice(self, count: int) -> list[int]:
        return sorted([random.randint(1, 6) for _ in range(count)], reverse=True)

    def roll_attacker(self, num_dice: int) -> list[int]:
        max_dice = min(self.MAX_ATTACKER_DICE, self.attacking_territory.troops - 1)
        num_dice = max(1, min(num_dice, max_dice))
        self.attacker_dice_num = num_dice
        self.attacker_dice = self.roll_dice(num_dice)
        return self.attacker_dice

    def roll_defender(self) -> list[int]:
        max_dice = min(self.MAX_DEFENDER_DICE, self.defending_territory.troops)
        self.defender_dice_num = max_dice
        self.defender_dice = self.roll_dice(max_dice)
        return self.defender_dice

    def resolve_combat(self) -> tuple[int, int]:
        attacker_losses = 0
        defender_losses = 0

        pairs = zip(self.attacker_dice, self.defender_dice)
        for atk, dfn in pairs:
            if atk > dfn:
                defender_losses += 1
            else:  # Gleichstand -> Verteidiger gewinnt
                attacker_losses += 1

        self.last_attacker_losses = attacker_losses
        self.last_defender_losses = defender_losses

        self.attacking_territory.troops -= attacker_losses
        self.defending_territory.troops -= defender_losses

        return attacker_losses, defender_losses

    def check_conquest(self) -> bool:
        return self.defending_territory.troops <= 0

    def conquer(self, troops_to_move: int):
        self.defending_territory.owner = self.attacking_territory.owner
        self.defending_territory.troops = troops_to_move
        self.attacking_territory.troops -= troops_to_move

    def can_continue_attack(self) -> bool:
        return self.attacking_territory.troops >= 2

