import sys
import pygame

from combat import Combat
from initializer import GameInitializer
from map_loader import MapLoader
from player import Player
from player_select import PLAYER_COLORS
from territory import WIDTH, HEIGHT
from turn_manager import TurnManager


class Game:
    def __init__(self, num_players: int):
        self.quit_rect = None
        self.running = None
        self.resume_rect = None

        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
        pygame.display.set_caption("Risk Map")

        self.font = pygame.font.SysFont("Arial", 22, bold=True)
        self.font_large = pygame.font.SysFont("Arial", 48, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 18)

        self.territories = MapLoader.load_territories()
        self.num_players = num_players
        self.player_colors = PLAYER_COLORS[:num_players]
        self.selected = None
        self.show_menu = False

        self.show_turn_overlay = True
        self.turn_overlay_continue_rect = None

        self.players = [
            Player(f"Spieler {i + 1}", self.player_colors[i])
            for i in range(num_players)
        ]

        self.turn_manager = TurnManager(self.players)

        self.selected_attacker = None
        self.active_combat: Combat | None = None
        self.attack_subphase: str | None = None
        self.pending_dice_count: int | None = None

        self.combat_last_conquered = False
        self.combat_last_can_continue = False

        self.attack_intro_continue_rect = None
        self.attack_defender_intro_continue_rect = None
        self.combat_dice_rects = {}
        self.combat_roll_rect = None
        self.combat_result_continue_rect = None
        self.combat_result_end_rect = None
        self.attack_end_phase_rect = None

        self.move_source = None
        self.move_target = None
        self.move_count = 1

        self.move_plus_rect = None
        self.move_minus_rect = None
        self.move_confirm_rect = None
        self.move_skip_rect = None

        self._assign_territories()
        self._start_placement_phase()

    def _assign_territories(self) -> None:
        assignments = GameInitializer.distribute_countries(self.num_players)
        name_to_territory = {t.name: t for t in self.territories}

        for player_index, country_names in enumerate(assignments):
            player = self.players[player_index]
            for name in country_names:
                if name in name_to_territory:
                    territory = name_to_territory[name]
                    territory.set_owner(player_index, self.player_colors)
                    player.add_territory(territory)

    def _start_placement_phase(self) -> None:
        player = self.turn_manager.get_current_player()
        player.calculate_reinforcements()
        self.turn_manager.set_phase("placement")
        self.show_turn_overlay = True

        self.selected = None
        self.selected_attacker = None
        self.active_combat = None
        self.attack_subphase = None
        self.pending_dice_count = None

        self.move_source = None
        self.move_target = None
        self.move_count = 1

    def _start_attack_phase(self) -> None:
        self.turn_manager.set_phase("attack")
        self.attack_subphase = "intro"

        self.selected = None
        self.selected_attacker = None
        self.active_combat = None
        self.pending_dice_count = None

    def _start_move_phase(self) -> None:
        self.turn_manager.set_phase("move")

        self.selected = None
        self.selected_attacker = None
        self.attack_subphase = None
        self.active_combat = None
        self.pending_dice_count = None

        self.move_source = None
        self.move_target = None
        self.move_count = 1

    def _finish_move_phase(self) -> None:
        self.move_source = None
        self.move_target = None
        self.move_count = 1
        self._end_turn()

    def _end_turn(self) -> None:
        self.turn_manager.next_player()

        while not self.turn_manager.get_current_player().life:
            self.turn_manager.next_player()

        self._start_placement_phase()

    def handle_click(self, pos) -> None:
        phase = self.turn_manager.phase
        current_player = self.turn_manager.get_current_player()
        current_index = self.turn_manager.current_index

        if phase == "placement":
            for t in self.territories:
                if t.contains(pos):
                    if t.owner == current_index:
                        if current_player.reinforcements > 0:
                            t.troops += 1
                            current_player.reinforcements -= 1

                            if current_player.reinforcements == 0:
                                self._start_attack_phase()
                    else:
                        print("Das ist nicht dein Land!")

                    self.selected = t
                    break

        elif phase == "attack" and self.attack_subphase == "select_attacker":
            if self.attack_end_phase_rect and self.attack_end_phase_rect.collidepoint(pos):
                self._start_move_phase()
                return

            for t in self.territories:
                if not t.contains(pos):
                    continue

                if t.owner == current_index:
                    if t.troops >= 2:
                        self.selected_attacker = t
                        self.selected = t
                        self.attack_subphase = "select_defender_intro"
                    else:
                        print(f"{t.name} hat zu wenig Truppen.")

                break

        elif phase == "attack" and self.attack_subphase == "select_defender":
            for t in self.territories:
                if not t.contains(pos):
                    continue

                if (
                    t.owner != current_index
                    and t.name in self.selected_attacker.neighbors
                ):
                    max_dice = min(
                        Combat.MAX_ATTACKER_DICE,
                        self.selected_attacker.troops - 1
                    )
                    self.active_combat = Combat(self.selected_attacker, t, self.players)
                    self.pending_dice_count = max_dice
                    self.attack_subphase = "combat_roll"

                elif t == self.selected_attacker:
                    self.attack_subphase = "select_attacker"
                    self.selected = None
                    self.selected_attacker = None

                elif t.owner == current_index and t.troops >= 2:
                    self.selected_attacker = t
                    self.selected = t
                    self.attack_subphase = "select_defender_intro"

                break

        elif phase == "move":
            if self.move_skip_rect and self.move_skip_rect.collidepoint(pos):
                self._finish_move_phase()
                return

            if self.move_source and self.move_target:
                max_move = self.move_source.troops - 1

                if self.move_minus_rect and self.move_minus_rect.collidepoint(pos):
                    self.move_count = max(1, self.move_count - 1)
                    return

                if self.move_plus_rect and self.move_plus_rect.collidepoint(pos):
                    self.move_count = min(max_move, self.move_count + 1)
                    return

                if self.move_confirm_rect and self.move_confirm_rect.collidepoint(pos):
                    self.move_source.troops -= self.move_count
                    self.move_target.troops += self.move_count
                    self._finish_move_phase()
                    return

            for t in self.territories:
                if not t.contains(pos):
                    continue

                if self.move_source is None:
                    if t.owner == current_index and t.troops >= 2:
                        self.move_source = t
                        self.selected = t
                        self.move_count = 1
                    else:
                        print("Waehle ein eigenes Land mit mindestens 2 Truppen.")

                    break

                elif self.move_target is None:
                    if (
                        t.owner == current_index
                        and t != self.move_source
                        and t.name in self.move_source.neighbors
                    ):
                        self.move_target = t
                        self.selected = t
                        self.move_count = 1

                    elif t == self.move_source:
                        self.move_source = None
                        self.selected = None

                    else:
                        print("Ziel muss ein eigenes Nachbarland sein.")

                    break

    def _handle_attack_overlay_click(self, pos) -> None:
        subphase = self.attack_subphase

        if subphase == "intro":
            if self.attack_intro_continue_rect and self.attack_intro_continue_rect.collidepoint(pos):
                self.attack_subphase = "select_attacker"

        elif subphase == "select_defender_intro":
            if self.attack_defender_intro_continue_rect and self.attack_defender_intro_continue_rect.collidepoint(pos):
                self.attack_subphase = "select_defender"

        elif subphase == "combat_roll":
            combat = self.active_combat
            max_dice = min(Combat.MAX_ATTACKER_DICE, combat.attacking_territory.troops - 1)

            for count, rect in self.combat_dice_rects.items():
                if rect.collidepoint(pos) and count <= max_dice:
                    self.pending_dice_count = count
                    return

            if self.combat_roll_rect and self.combat_roll_rect.collidepoint(pos):
                combat.fight(self.pending_dice_count)
                self.combat_last_conquered = combat.check_conquest()
                self.combat_last_can_continue = (
                    combat.can_continue_attack()
                    if not self.combat_last_conquered
                    else False
                )
                self.attack_subphase = "combat_result"

        elif subphase == "combat_result":
            if self.combat_result_continue_rect and self.combat_result_continue_rect.collidepoint(pos):
                if self.combat_last_conquered or not self.combat_last_can_continue:
                    self._end_combat()
                else:
                    self.pending_dice_count = min(
                        Combat.MAX_ATTACKER_DICE,
                        self.active_combat.attacking_territory.troops - 1
                    )
                    self.attack_subphase = "combat_roll"

            elif self.combat_result_end_rect and self.combat_result_end_rect.collidepoint(pos):
                self._end_combat()

    def _end_combat(self) -> None:
        if self.active_combat.check_conquest():
            self.active_combat.conquer(self.active_combat.attacker_dice_num)

        self.active_combat = None
        self.selected_attacker = None
        self.selected = None
        self.pending_dice_count = None
        self.combat_last_conquered = False
        self.combat_last_can_continue = False
        self.attack_subphase = "select_attacker"

    def handle_menu_click(self, pos) -> None:
        if self.resume_rect and self.resume_rect.collidepoint(pos):
            self.show_menu = False

        if self.quit_rect and self.quit_rect.collidepoint(pos):
            self.running = False

    def run(self) -> None:
        clock = pygame.time.Clock()
        self.running = True

        while self.running:
            clock.tick(60)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE and not self.show_turn_overlay:
                        self.show_menu = not self.show_menu

                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()

                    attack_modal = (
                        self.turn_manager.phase == "attack"
                        and self.attack_subphase in (
                            "intro",
                            "select_defender_intro",
                            "combat_roll",
                            "combat_result",
                        )
                    )

                    if self.show_turn_overlay:
                        if (
                            self.turn_overlay_continue_rect
                            and self.turn_overlay_continue_rect.collidepoint(mouse_pos)
                        ):
                            self.show_turn_overlay = False

                    elif self.show_menu:
                        self.handle_menu_click(mouse_pos)

                    elif attack_modal:
                        self._handle_attack_overlay_click(mouse_pos)

                    else:
                        self.handle_click(mouse_pos)

            self.draw()

        pygame.quit()
        sys.exit()

    def draw(self) -> None:
        self.screen.fill((30, 100, 160))

        for t in self.territories:
            t.draw(self.screen, self.font)

        if self.selected_attacker and self.attack_subphase in (
            "select_defender_intro",
            "select_defender",
            "combat_roll",
            "combat_result",
        ):
            self._draw_territory_outline(self.selected_attacker, (255, 255, 100), 5)

        if self.attack_subphase == "select_defender":
            self._draw_valid_defender_highlights()

        if self.turn_manager.phase == "move":
            self._draw_move_highlights()

        if self.selected:
            name = self.selected.name.replace("_", " ").title()
            shadow = self.font.render(name, True, (0, 0, 0))
            text = self.font.render(name, True, (255, 255, 255))
            self.screen.blit(shadow, (12, 12))
            self.screen.blit(text, (10, 10))

        attack_modal = (
            self.turn_manager.phase == "attack"
            and self.attack_subphase in (
                "intro",
                "select_defender_intro",
                "combat_roll",
                "combat_result",
            )
        )

        if not self.show_turn_overlay and not self.show_menu and not attack_modal:
            self._draw_hud()

        if self.show_turn_overlay:
            self._draw_turn_overlay()

        elif self.show_menu:
            self._draw_menu()

        elif attack_modal:
            draw_map = {
                "intro": self._draw_attack_intro_overlay,
                "select_defender_intro": self._draw_attack_select_defender_overlay,
                "combat_roll": self._draw_combat_roll_overlay,
                "combat_result": self._draw_combat_result_overlay,
            }
            draw_map[self.attack_subphase]()

        pygame.display.flip()

    def _draw_hud(self) -> None:
        player = self.turn_manager.get_current_player()
        phase = self.turn_manager.phase

        panel_w, panel_h = 360, 110
        panel_x = WIDTH - panel_w - 20
        panel_y = 20

        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 160))
        self.screen.blit(panel, (panel_x, panel_y))

        pygame.draw.rect(self.screen, player.color, (panel_x, panel_y, 8, panel_h))

        name_surf = self.font.render(player.name, True, player.color)
        self.screen.blit(name_surf, (panel_x + 18, panel_y + 10))

        if phase == "placement":
            self.screen.blit(
                self.font_small.render("Phase: Truppen setzen", True, (200, 200, 200)),
                (panel_x + 18, panel_y + 38),
            )

            troop_label = self.font_small.render("Noch zu setzen:", True, (200, 200, 200))
            troop_num = self.font_large.render(str(player.reinforcements), True, (255, 230, 80))

            self.screen.blit(troop_label, (panel_x + 18, panel_y + 62))
            self.screen.blit(
                troop_num,
                (
                    panel_x + panel_w - troop_num.get_width() - 15,
                    panel_y + panel_h // 2 - troop_num.get_height() // 2,
                ),
            )

        elif phase == "attack":
            self._draw_attack_hud(panel_x, panel_y, panel_w, panel_h)

        elif phase == "move":
            self._draw_move_hud(panel_x, panel_y, panel_w, panel_h)

    def _draw_attack_hud(self, panel_x: int, panel_y: int, panel_w: int, panel_h: int) -> None:
        subphase = self.attack_subphase

        if subphase == "select_attacker":
            self.screen.blit(
                self.font_small.render("Phase: Angriff - Angreifer waehlen", True, (200, 200, 200)),
                (panel_x + 18, panel_y + 38),
            )

            btn_w, btn_h = 320, 34
            btn_x = panel_x + 18
            btn_y = panel_y + panel_h + 10

            self.attack_end_phase_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)

            hover = self.attack_end_phase_rect.collidepoint(pygame.mouse.get_pos())
            pygame.draw.rect(
                self.screen,
                (80, 100, 80) if hover else (55, 75, 55),
                self.attack_end_phase_rect,
                border_radius=6,
            )

            end_txt = self.font_small.render("Zur Truppenbewegung", True, (200, 230, 200))
            self.screen.blit(
                end_txt,
                (
                    btn_x + btn_w // 2 - end_txt.get_width() // 2,
                    btn_y + btn_h // 2 - end_txt.get_height() // 2,
                ),
            )

        elif subphase == "select_defender":
            self.screen.blit(
                self.font_small.render("Phase: Angriff - Ziel waehlen", True, (200, 200, 200)),
                (panel_x + 18, panel_y + 38),
            )

            if self.selected_attacker:
                att_txt = self.font_small.render(
                    f"Angreifer: {self.selected_attacker.name.replace('_', ' ').title()}",
                    True,
                    (255, 230, 80),
                )
                self.screen.blit(att_txt, (panel_x + 18, panel_y + 62))

            self.attack_end_phase_rect = None

        else:
            self.attack_end_phase_rect = None

    def _draw_move_hud(self, panel_x: int, panel_y: int, panel_w: int, panel_h: int) -> None:
        self.screen.blit(
            self.font_small.render("Phase: Truppen verschieben", True, (200, 200, 200)),
            (panel_x + 18, panel_y + 38),
        )

        if not self.move_source:
            info = "Quelle mit mind. 2 Truppen waehlen"
        elif not self.move_target:
            info = "Eigenes Nachbarland waehlen"
        else:
            info = f"{self.move_count} Truppen verschieben"

        self.screen.blit(
            self.font_small.render(info, True, (255, 230, 80)),
            (panel_x + 18, panel_y + 62),
        )

        btn_w, btn_h = 320, 34
        btn_x = panel_x + 18
        btn_y = panel_y + panel_h + 10

        self.move_skip_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)

        hover = self.move_skip_rect.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(
            self.screen,
            (80, 100, 80) if hover else (55, 75, 55),
            self.move_skip_rect,
            border_radius=6,
        )

        skip_txt = self.font_small.render("Zug beenden", True, (200, 230, 200))
        self.screen.blit(
            skip_txt,
            (
                btn_x + btn_w // 2 - skip_txt.get_width() // 2,
                btn_y + btn_h // 2 - skip_txt.get_height() // 2,
            ),
        )

        if self.move_source and self.move_target:
            self._draw_move_controls(panel_x, panel_y + panel_h + 55)

    def _draw_move_controls(self, x: int, y: int) -> None:
        max_move = self.move_source.troops - 1
        self.move_count = max(1, min(self.move_count, max_move))

        btn_size = 38

        self.move_minus_rect = pygame.Rect(x + 18, y, btn_size, btn_size)
        self.move_plus_rect = pygame.Rect(x + 118, y, btn_size, btn_size)
        self.move_confirm_rect = pygame.Rect(x + 18, y + 48, 220, 38)

        mx, my = pygame.mouse.get_pos()

        for label, rect in [
            ("-", self.move_minus_rect),
            ("+", self.move_plus_rect),
        ]:
            hover = rect.collidepoint(mx, my)
            pygame.draw.rect(
                self.screen,
                (90, 90, 110) if hover else (65, 65, 85),
                rect,
                border_radius=6,
            )

            txt = self.font.render(label, True, (255, 255, 255))
            self.screen.blit(
                txt,
                (
                    rect.x + rect.w // 2 - txt.get_width() // 2,
                    rect.y + rect.h // 2 - txt.get_height() // 2,
                ),
            )

        count_txt = self.font.render(str(self.move_count), True, (255, 230, 80))
        self.screen.blit(count_txt, (x + 82, y + 5))

        hover = self.move_confirm_rect.collidepoint(mx, my)
        pygame.draw.rect(
            self.screen,
            (80, 130, 80) if hover else (55, 95, 55),
            self.move_confirm_rect,
            border_radius=6,
        )

        confirm_txt = self.font_small.render("Verschieben", True, (230, 255, 230))
        self.screen.blit(
            confirm_txt,
            (
                self.move_confirm_rect.x + self.move_confirm_rect.w // 2 - confirm_txt.get_width() // 2,
                self.move_confirm_rect.y + self.move_confirm_rect.h // 2 - confirm_txt.get_height() // 2,
            ),
        )

    def _draw_move_highlights(self) -> None:
        current_index = self.turn_manager.current_index

        if self.move_source:
            self._draw_territory_outline(self.move_source, (120, 220, 255), 5)

        if self.move_target:
            self._draw_territory_outline(self.move_target, (100, 255, 140), 5)

        if self.move_source and not self.move_target:
            for t in self.territories:
                if (
                    t.owner == current_index
                    and t != self.move_source
                    and t.name in self.move_source.neighbors
                ):
                    self._draw_territory_outline(t, (100, 255, 140), 5)

    def _draw_turn_overlay(self) -> None:
        player = self.turn_manager.get_current_player()

        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))

        card_w, card_h = 500, 280
        card_x = WIDTH // 2 - card_w // 2
        card_y = HEIGHT // 2 - card_h // 2

        card = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
        card.fill((20, 20, 30, 240))
        self.screen.blit(card, (card_x, card_y))

        pygame.draw.rect(self.screen, player.color, (card_x, card_y, card_w, 8))
        pygame.draw.rect(self.screen, player.color, (card_x, card_y, card_w, card_h), 3)

        self.screen.blit(
            self.font_small.render("DU BIST DRAN", True, (180, 180, 180)),
            (
                card_x + card_w // 2 - self.font_small.size("DU BIST DRAN")[0] // 2,
                card_y + 25,
            ),
        )

        name_surf = self.font_large.render(player.name, True, player.color)
        self.screen.blit(
            name_surf,
            (card_x + card_w // 2 - name_surf.get_width() // 2, card_y + 60),
        )

        reinf_surf = self.font.render(
            f"Truppen zu setzen: {player.reinforcements}",
            True,
            (255, 230, 80),
        )
        self.screen.blit(
            reinf_surf,
            (card_x + card_w // 2 - reinf_surf.get_width() // 2, card_y + 140),
        )

        hint = self.font_small.render(
            "Klicke auf deine Laender um Truppen zu setzen",
            True,
            (160, 160, 160),
        )
        self.screen.blit(
            hint,
            (card_x + card_w // 2 - hint.get_width() // 2, card_y + 180),
        )

        btn_w, btn_h = 200, 45
        btn_x = card_x + card_w // 2 - btn_w // 2
        btn_y = card_y + card_h - btn_h - 20

        self.turn_overlay_continue_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)

        hover = self.turn_overlay_continue_rect.collidepoint(pygame.mouse.get_pos())
        btn_color = tuple(min(255, c + 50) for c in player.color) if hover else player.color

        pygame.draw.rect(
            self.screen,
            btn_color,
            self.turn_overlay_continue_rect,
            border_radius=8,
        )

        btn_txt = self.font.render("Los geht's!", True, (255, 255, 255))
        self.screen.blit(
            btn_txt,
            (
                btn_x + btn_w // 2 - btn_txt.get_width() // 2,
                btn_y + btn_h // 2 - btn_txt.get_height() // 2,
            ),
        )

    def _draw_attack_intro_overlay(self) -> None:
        player = self.turn_manager.get_current_player()

        self._draw_overlay_card((25, 10, 10), (180, 40, 40), 560, 310)

        card_x = WIDTH // 2 - 280
        card_y = HEIGHT // 2 - 155

        self._blit_centered(
            self.font_small.render("ANGRIFFSPHASE", True, (180, 100, 100)),
            card_y + 25,
        )
        self._blit_centered(
            self.font_large.render(player.name, True, player.color),
            card_y + 58,
        )

        pygame.draw.line(
            self.screen,
            (80, 40, 40),
            (card_x + 30, card_y + 120),
            (card_x + 530, card_y + 120),
            1,
        )

        self._blit_centered(
            self.font.render("Waehle ein Territorium, das angreift", True, (230, 220, 220)),
            card_y + 138,
        )
        self._blit_centered(
            self.font_small.render("(mind. 2 Truppen erforderlich)", True, (150, 130, 130)),
            card_y + 175,
        )

        self.attack_intro_continue_rect = self._draw_button(
            "Los geht's!",
            card_x,
            card_y + 242,
            560,
            (170, 35, 35),
            (220, 70, 70),
        )

    def _draw_attack_select_defender_overlay(self) -> None:
        player = self.turn_manager.get_current_player()
        attacker = self.selected_attacker

        self._draw_overlay_card((25, 10, 10), (180, 40, 40), 580, 310)

        card_x = WIDTH // 2 - 290
        card_y = HEIGHT // 2 - 155

        self._blit_centered(
            self.font_small.render("ANGREIFER GEWAEHLT", True, (180, 100, 100)),
            card_y + 22,
        )
        self._blit_centered(
            self.font_large.render(attacker.name.replace("_", " ").title(), True, player.color),
            card_y + 55,
        )
        self._blit_centered(
            self.font.render(f"{attacker.troops} Truppen verfuegbar", True, (255, 230, 80)),
            card_y + 115,
        )

        pygame.draw.line(
            self.screen,
            (80, 40, 40),
            (card_x + 30, card_y + 148),
            (card_x + 550, card_y + 148),
            1,
        )

        self._blit_centered(
            self.font.render("Waehle das Territorium, das du angreifen moechtest", True, (230, 220, 220)),
            card_y + 165,
        )

        self.attack_defender_intro_continue_rect = self._draw_button(
            "Weiter",
            card_x,
            card_y + 242,
            580,
            (170, 35, 35),
            (220, 70, 70),
        )

    def _draw_combat_roll_overlay(self) -> None:
        combat = self.active_combat
        player = self.turn_manager.get_current_player()
        attacker = combat.attacking_territory
        defender = combat.defending_territory

        max_dice = min(Combat.MAX_ATTACKER_DICE, attacker.troops - 1)

        if self.pending_dice_count is None or self.pending_dice_count > max_dice:
            self.pending_dice_count = max_dice

        self._draw_overlay_card((20, 12, 12), (180, 40, 40), 720, 420)

        card_x = WIDTH // 2 - 360
        card_y = HEIGHT // 2 - 210

        self._blit_centered(
            self.font_large.render("KAMPF!", True, (220, 60, 60)),
            card_y + 18,
        )

        pygame.draw.line(
            self.screen,
            (80, 30, 30),
            (card_x + 30, card_y + 78),
            (card_x + 690, card_y + 78),
            1,
        )

        self.screen.blit(
            self.font.render(attacker.name.replace("_", " ").title(), True, player.color),
            (card_x + 40, card_y + 90),
        )
        self.screen.blit(
            self.font_large.render(str(attacker.troops), True, (255, 230, 80)),
            (card_x + 40, card_y + 122),
        )

        vs = self.font_large.render("VS", True, (160, 140, 140))
        self.screen.blit(vs, (WIDTH // 2 - vs.get_width() // 2, card_y + 130))

        def_player = self.players[defender.owner] if defender.owner is not None else None
        def_color = def_player.color if def_player else (200, 200, 200)

        def_txt = self.font.render(defender.name.replace("_", " ").title(), True, def_color)
        self.screen.blit(def_txt, (card_x + 720 - 40 - def_txt.get_width(), card_y + 90))

        def_num = self.font_large.render(str(defender.troops), True, (255, 230, 80))
        self.screen.blit(def_num, (card_x + 720 - 40 - def_num.get_width(), card_y + 122))

        pygame.draw.line(
            self.screen,
            (80, 30, 30),
            (card_x + 30, card_y + 205),
            (card_x + 690, card_y + 205),
            1,
        )

        self._blit_centered(
            self.font_small.render("Wuerfelanzahl waehlen:", True, (200, 180, 180)),
            card_y + 218,
        )

        self.combat_dice_rects = {}

        btn_w2, btn_h2 = 80, 46
        start_x = WIDTH // 2 - (3 * btn_w2 + 2 * 14) // 2
        mx, my = pygame.mouse.get_pos()

        for i in range(1, 4):
            bx = start_x + (i - 1) * (btn_w2 + 14)
            by = card_y + 248

            rect = pygame.Rect(bx, by, btn_w2, btn_h2)
            available = i <= max_dice
            selected = i == self.pending_dice_count

            self.combat_dice_rects[i] = rect

            if not available:
                bg, fg = (45, 35, 35), (90, 70, 70)
            elif selected:
                bg, fg = (200, 50, 50), (255, 255, 255)
            else:
                bg = (100, 50, 50) if rect.collidepoint(mx, my) else (70, 35, 35)
                fg = (255, 255, 255)

            pygame.draw.rect(self.screen, bg, rect, border_radius=8)

            if available:
                border_col = (180, 40, 40) if selected else (120, 60, 60)
                pygame.draw.rect(self.screen, border_col, rect, 2, border_radius=8)

            d_txt = self.font_large.render(str(i), True, fg)
            self.screen.blit(
                d_txt,
                (
                    bx + btn_w2 // 2 - d_txt.get_width() // 2,
                    by + btn_h2 // 2 - d_txt.get_height() // 2,
                ),
            )

        self.combat_roll_rect = self._draw_button(
            "WUERFELN!",
            card_x,
            card_y + 352,
            720,
            (180, 35, 35),
            (230, 80, 80),
            font=self.font,
        )

    def _draw_combat_result_overlay(self) -> None:
        combat = self.active_combat
        player = self.turn_manager.get_current_player()
        attacker = combat.attacking_territory
        defender = combat.defending_territory

        def_player = self.players[defender.owner] if defender.owner is not None else None
        def_color = def_player.color if def_player else (200, 200, 200)

        self._draw_overlay_card((20, 12, 12), (180, 40, 40), 740, 500)

        card_x = WIDTH // 2 - 370
        card_y = HEIGHT // 2 - 250

        self._blit_centered(
            self.font_large.render("WUERFELERGEBNIS", True, (220, 60, 60)),
            card_y + 18,
        )

        pygame.draw.line(
            self.screen,
            (80, 30, 30),
            (card_x + 30, card_y + 78),
            (card_x + 710, card_y + 78),
            1,
        )

        self.screen.blit(
            self.font.render(attacker.name.replace("_", " ").title(), True, player.color),
            (card_x + 40, card_y + 90),
        )

        for i, d in enumerate(combat.attacker_dice):
            self._draw_die(card_x + 40 + i * 82, card_y + 125, d, (180, 40, 40))

        loss_a = self.font.render(
            f"Verluste: -{combat.last_attacker_losses}",
            True,
            (255, 90, 90) if combat.last_attacker_losses > 0 else (100, 180, 100),
        )
        self.screen.blit(loss_a, (card_x + 40, card_y + 210))

        self.screen.blit(
            self.font_small.render(f"Verbleibend: {attacker.troops} Truppen", True, (200, 200, 200)),
            (card_x + 40, card_y + 245),
        )

        pygame.draw.line(
            self.screen,
            (80, 30, 30),
            (WIDTH // 2, card_y + 88),
            (WIDTH // 2, card_y + 275),
            1,
        )

        def_lbl = self.font.render(defender.name.replace("_", " ").title(), True, def_color)
        self.screen.blit(def_lbl, (card_x + 740 - 40 - def_lbl.get_width(), card_y + 90))

        die_start_x = card_x + 740 - 40 - len(combat.defender_dice) * 82 + (82 - 60)

        for i, d in enumerate(combat.defender_dice):
            self._draw_die(die_start_x + i * 82, card_y + 125, d, (40, 80, 180))

        loss_d = self.font.render(
            f"Verluste: -{combat.last_defender_losses}",
            True,
            (255, 90, 90) if combat.last_defender_losses > 0 else (100, 180, 100),
        )
        self.screen.blit(loss_d, (card_x + 740 - 40 - loss_d.get_width(), card_y + 210))

        defender_info = f"Verbleibend: {defender.troops} Truppen"
        self.screen.blit(
            self.font_small.render(defender_info, True, (200, 200, 200)),
            (
                card_x + 740 - 40 - self.font_small.size(defender_info)[0],
                card_y + 245,
            ),
        )

        pygame.draw.line(
            self.screen,
            (80, 30, 30),
            (card_x + 30, card_y + 285),
            (card_x + 710, card_y + 285),
            1,
        )

        if self.combat_last_conquered:
            status = self.font_large.render("TERRITORIUM EROBERT!", True, (255, 210, 50))
            self.screen.blit(status, (WIDTH // 2 - status.get_width() // 2, card_y + 305))

        elif not self.combat_last_can_continue:
            status = self.font.render(
                "Zu wenig Truppen - Angriff wird abgebrochen.",
                True,
                (200, 150, 150),
            )
            self.screen.blit(status, (WIDTH // 2 - status.get_width() // 2, card_y + 315))

        btn_h = 50

        if self.combat_last_conquered or not self.combat_last_can_continue:
            c = (200, 160, 30) if self.combat_last_conquered else (60, 80, 100)
            c_h = (230, 190, 50) if self.combat_last_conquered else (80, 100, 130)

            self.combat_result_continue_rect = self._draw_button(
                "Weiter",
                card_x,
                card_y + 430,
                740,
                c,
                c_h,
            )
            self.combat_result_end_rect = None

        else:
            btn_w = 240
            gap = 20

            bx1 = WIDTH // 2 - (btn_w * 2 + gap) // 2
            bx2 = bx1 + btn_w + gap
            by = card_y + 430

            self.combat_result_continue_rect = pygame.Rect(bx1, by, btn_w, btn_h)
            self.combat_result_end_rect = pygame.Rect(bx2, by, btn_w, btn_h)

            mx, my = pygame.mouse.get_pos()

            pygame.draw.rect(
                self.screen,
                (220, 70, 70)
                if self.combat_result_continue_rect.collidepoint(mx, my)
                else (170, 35, 35),
                self.combat_result_continue_rect,
                border_radius=10,
            )

            cont_txt = self.font.render("Weiterkaempfen", True, (255, 255, 255))
            self.screen.blit(
                cont_txt,
                (
                    bx1 + btn_w // 2 - cont_txt.get_width() // 2,
                    by + btn_h // 2 - cont_txt.get_height() // 2,
                ),
            )

            pygame.draw.rect(
                self.screen,
                (75, 85, 100)
                if self.combat_result_end_rect.collidepoint(mx, my)
                else (55, 65, 80),
                self.combat_result_end_rect,
                border_radius=10,
            )

            end_txt = self.font.render("Angriff beenden", True, (200, 210, 220))
            self.screen.blit(
                end_txt,
                (
                    bx2 + btn_w // 2 - end_txt.get_width() // 2,
                    by + btn_h // 2 - end_txt.get_height() // 2,
                ),
            )

    def _draw_menu(self) -> None:
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        title = self.font.render("MENUE", True, (255, 255, 255))
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 2 - 150))

        self.resume_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 - 20, 200, 40)
        self.quit_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 40, 200, 40)

        pygame.draw.rect(self.screen, (80, 80, 80), self.resume_rect)
        pygame.draw.rect(self.screen, (120, 50, 50), self.quit_rect)

        for text, rect in [
            ("Weiter", self.resume_rect),
            ("Beenden", self.quit_rect),
        ]:
            surf = self.font.render(text, True, (255, 255, 255))
            self.screen.blit(
                surf,
                (
                    rect.x + rect.w // 2 - surf.get_width() // 2,
                    rect.y + rect.h // 2 - surf.get_height() // 2,
                ),
            )

    def _draw_die(self, x: int, y: int, value: int, color: tuple) -> None:
        size = 60

        pygame.draw.rect(self.screen, color, (x, y, size, size), border_radius=10)
        pygame.draw.rect(self.screen, (255, 255, 255), (x, y, size, size), 2, border_radius=10)

        num = self.font_large.render(str(value), True, (255, 255, 255))
        self.screen.blit(
            num,
            (
                x + size // 2 - num.get_width() // 2,
                y + size // 2 - num.get_height() // 2,
            ),
        )

    def _draw_overlay_card(self, fill: tuple, border: tuple, card_w: int, card_h: int) -> None:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 210))
        self.screen.blit(overlay, (0, 0))

        card_x = WIDTH // 2 - card_w // 2
        card_y = HEIGHT // 2 - card_h // 2

        card = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
        card.fill((*fill, 245))
        self.screen.blit(card, (card_x, card_y))

        pygame.draw.rect(self.screen, border, (card_x, card_y, card_w, 8))
        pygame.draw.rect(self.screen, border, (card_x, card_y, card_w, card_h), 3)

    def _blit_centered(self, surface, y: int) -> None:
        self.screen.blit(surface, (WIDTH // 2 - surface.get_width() // 2, y))

    def _draw_button(
        self,
        label: str,
        card_x: int,
        card_y_offset: int,
        card_w: int,
        color_normal: tuple,
        color_hover: tuple,
        font=None,
    ) -> pygame.Rect:
        font = font or self.font

        btn_w, btn_h = 240, 52
        btn_x = card_x + card_w // 2 - btn_w // 2
        btn_y = card_y_offset

        rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
        hover = rect.collidepoint(pygame.mouse.get_pos())

        pygame.draw.rect(
            self.screen,
            color_hover if hover else color_normal,
            rect,
            border_radius=10,
        )

        txt = font.render(label, True, (255, 255, 255))
        self.screen.blit(
            txt,
            (
                btn_x + btn_w // 2 - txt.get_width() // 2,
                btn_y + btn_h // 2 - txt.get_height() // 2,
            ),
        )

        return rect

    def _draw_territory_outline(self, territory, color: tuple, width: int) -> None:
        valid = [
            (x, y)
            for x, y in territory.points
            if 0 <= x <= WIDTH and 0 <= y <= HEIGHT
        ]

        if len(valid) >= 3:
            try:
                pygame.draw.polygon(self.screen, color, valid, width)
            except Exception:
                pass

    def _draw_valid_defender_highlights(self) -> None:
        if not self.selected_attacker:
            return

        current_index = self.turn_manager.current_index

        for t in self.territories:
            is_enemy = t.owner != current_index
            is_neighbor = t.name in self.selected_attacker.neighbors

            if is_enemy and is_neighbor:
                self._draw_territory_outline(t, (255, 80, 80), 6)
                self._draw_territory_outline(t, (255, 220, 120), 2)