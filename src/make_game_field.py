import pygame
import sys
import json
import xml.etree.ElementTree as ET
from svgpathtools import parse_path
import initialCountries
from player_select import PLAYER_COLORS
from player import Player
from turn_manager import TurnManager
from combat import Combat

WIDTH = 1920
HEIGHT = 1080

SVG_WIDTH = 749.81909
SVG_HEIGHT = 519.06781
OFFSET_X = -167.99651
OFFSET_Y = -118.55507

SCALE_X = WIDTH / SVG_WIDTH
SCALE_Y = HEIGHT / SVG_HEIGHT


def svg_to_screen(x, y):
    sx = (x + OFFSET_X) * SCALE_X
    sy = (y + OFFSET_Y) * SCALE_Y
    return sx, sy


def point_in_polygon(point, polygon):
    x, y = point
    inside = False
    j = len(polygon) - 1

    for i in range(len(polygon)):
        xi, yi = polygon[i]
        xj, yj = polygon[j]

        if (yi > y) != (yj > y):
            denom = yj - yi
            if abs(denom) > 0.00001:
                if x < (xj - xi) * (y - yi) / denom + xi:
                    inside = not inside
        j = i

    return inside


class Territory:
    def __init__(self, name, points, color):
        self.name = name
        self.points = points
        self.color = color
        self.border_color = (30, 30, 30)
        self.owner = None
        self.troops = 1

        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        self.center = (
            (min(xs) + max(xs)) / 2,
            (min(ys) + max(ys)) / 2
        )

    def set_owner(self, player_index, player_colors):
        self.owner = player_index
        self.border_color = player_colors[player_index]

    def contains(self, point):
        return point_in_polygon(point, self.points)

    def draw(self, screen, font):
        valid = [(x, y) for x, y in self.points if 0 <= x <= WIDTH and 0 <= y <= HEIGHT]
        if len(valid) < 3:
            return

        try:
            pygame.draw.polygon(screen, self.color, valid, 0)
            pygame.draw.polygon(screen, self.border_color, valid, 3)
        except Exception:
            pass

        num_color = self.border_color if self.owner is not None else (255, 255, 255)

        cx, cy = self.center
        shadow = font.render(str(self.troops), True, (0, 0, 0))
        text = font.render(str(self.troops), True, num_color)

        screen.blit(shadow, (
            cx - shadow.get_width() // 2 + 1,
            cy - shadow.get_height() // 2 + 1
        ))
        screen.blit(text, (
            cx - text.get_width() // 2,
            cy - text.get_height() // 2
        ))


class MapLoader:
    CONTINENT_COLORS = {
        "eastern_australia": (200, 100, 50),
        "western_australia": (200, 100, 50),
        "new_guinea": (200, 100, 50),
        "indonesia": (200, 100, 50),

        "alaska": (100, 180, 100),
        "ontario": (100, 180, 100),
        "northwest_territory": (100, 180, 100),
        "quebec": (100, 180, 100),
        "eastern_united_states": (100, 180, 100),
        "western_united_states": (100, 180, 100),
        "central_america": (100, 180, 100),
        "alberta": (100, 180, 100),
        "greenland": (100, 180, 100),

        "venezuela": (220, 180, 50),
        "brazil": (220, 180, 50),
        "peru": (220, 180, 50),
        "argentina": (220, 180, 50),

        "iceland": (150, 200, 220),
        "great_britain": (150, 200, 220),
        "scandinavia": (150, 200, 220),
        "northern_europe": (150, 200, 220),
        "western_europe": (150, 200, 220),
        "southern_europe": (150, 200, 220),
        "ukraine": (150, 200, 220),

        "north_africa": (220, 160, 80),
        "egypt": (220, 160, 80),
        "east_africa": (220, 160, 80),
        "congo": (220, 160, 80),
        "south_africa": (220, 160, 80),
        "madagascar": (220, 160, 80),

        "ural": (180, 120, 200),
        "siberia": (180, 120, 200),
        "yakutsk": (180, 120, 200),
        "kamchatka": (180, 120, 200),
        "irkutsk": (180, 120, 200),
        "mongolia": (180, 120, 200),
        "china": (180, 120, 200),
        "afghanistan": (180, 120, 200),
        "middle_east": (180, 120, 200),
        "india": (180, 120, 200),
        "siam": (180, 120, 200),
        "japan": (180, 120, 200),
    }

    @staticmethod
    def load_territories():
        tree = ET.parse("risk_map.svg")
        root = tree.getroot()

        territory_names = initialCountries.get_countries_from_json()
        territories = []

        for elem in root.iter("{http://www.w3.org/2000/svg}path"):
            territory_name = elem.get("id", "")
            if territory_name not in territory_names:
                continue

            d = elem.get("d", "")
            if not d:
                continue

            try:
                path = parse_path(d)
            except Exception:
                continue

            points = []
            for segment in path:
                x = segment.start.real
                y = segment.start.imag
                points.append(svg_to_screen(x, y))

            if len(points) < 3:
                continue

            color = MapLoader.CONTINENT_COLORS.get(territory_name, (180, 180, 180))
            territories.append(Territory(territory_name, points, color))

        print(f"Länder geladen: {len(territories)}")
        return territories


class Game:
    def __init__(self, num_players):
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
        print(self.players)

        with open("resources/continents.json", "r", encoding="utf-8") as f:
            self.continents_data = json.load(f)

        self.turn_manager = TurnManager(self.players)

        self._assign_territories()
        self._start_placement_phase()

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

    def _assign_territories(self):
        assignments = initialCountries.initial_countries_for_players(self.num_players)
        name_to_territory = {t.name: t for t in self.territories}

        for player_index, country_names in enumerate(assignments):
            player = self.players[player_index]
            for country_name in country_names:
                if country_name in name_to_territory:
                    territory = name_to_territory[country_name]
                    territory.set_owner(player_index, self.player_colors)
                    player.add_territory(territory)

    def _start_placement_phase(self):
        player = self.turn_manager.get_current_player()
        player.calculate_reinforcements(self.continents_data)
        self.turn_manager.set_phase("placement")
        self.show_turn_overlay = True

        self.selected_attacker = None
        self.active_combat = None
        self.attack_subphase = None
        self.pending_dice_count = None

    def _start_attack_phase(self):
        self.turn_manager.set_phase("attack")
        self.attack_subphase = "intro"
        self.selected_attacker = None
        self.selected = None
        self.active_combat = None
        self.pending_dice_count = None

    def handle_click(self, pos):
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
                            print(f"+1 Truppe auf {t.name} | Noch zu setzen: {current_player.reinforcements}")

                            if current_player.reinforcements == 0:
                                self._start_attack_phase()
                    else:
                        print("Das ist nicht dein Land!")
                    self.selected = t
                    break

        elif phase == "attack" and self.attack_subphase == "select_attacker":
            if self.attack_end_phase_rect and self.attack_end_phase_rect.collidepoint(pos):
                self._end_turn()
                return

            for t in self.territories:
                if not t.contains(pos):
                    continue
                if t.owner == current_index:
                    if t.troops >= 2:
                        self.selected_attacker = t
                        self.selected = t
                        self.attack_subphase = "select_defender_intro"
                        print(f"Angreifer: {t.name} ({t.troops} Truppen)")
                    else:
                        print(f"{t.name} hat zu wenig Truppen (mind. 2 nötig).")
                break

        elif phase == "attack" and self.attack_subphase == "select_defender":
            for t in self.territories:
                if not t.contains(pos):
                    continue
                if t.owner != current_index:
                    max_dice = min(Combat.MAX_ATTACKER_DICE, self.selected_attacker.troops - 1)
                    self.active_combat = Combat(self.selected_attacker, t, self.players)
                    self.pending_dice_count = max_dice
                    self.attack_subphase = "combat_roll"
                    print(f"Ziel: {t.name} ({t.troops} Truppen)")
                else:
                    if t.troops >= 2:
                        self.selected_attacker = t
                        self.selected = t
                        print(f"Angreifer geändert: {t.name}")
                break

    def _handle_attack_overlay_click(self, pos):
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
                self.combat_last_can_continue = combat.can_continue_attack() if not self.combat_last_conquered else False
                self.attack_subphase = "combat_result"
                print(
                    f"Würfel: {combat.attacker_dice} vs {combat.defender_dice} | "
                    f"Verluste → Ang: -{combat.last_attacker_losses}  "
                    f"Vert: -{combat.last_defender_losses}"
                )

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

    def _end_combat(self):
        self.active_combat = None
        self.selected_attacker = None
        self.selected = None
        self.pending_dice_count = None
        self.combat_last_conquered = False
        self.combat_last_can_continue = False
        self.attack_subphase = "select_attacker"

    def _end_turn(self):
        self.turn_manager.next_player()
        self._start_placement_phase()

    def draw(self):
        self.screen.fill((30, 100, 160))

        for t in self.territories:
            if t is self.selected_attacker and self.attack_subphase in (
                "select_defender_intro", "select_defender",
                "combat_roll", "combat_result"
            ):
                valid = [(x, y) for x, y in t.points if 0 <= x <= WIDTH and 0 <= y <= HEIGHT]
                if len(valid) >= 3:
                    try:
                        pygame.draw.polygon(self.screen, (255, 255, 100), valid, 5)
                    except Exception:
                        pass
            t.draw(self.screen, self.font)

        if self.selected:
            name = self.selected.name.replace("_", " ").title()
            shadow = self.font.render(name, True, (0, 0, 0))
            text = self.font.render(name, True, (255, 255, 255))
            self.screen.blit(shadow, (12, 12))
            self.screen.blit(text, (10, 10))

        attack_overlay = (
            self.turn_manager.phase == "attack" and
            self.attack_subphase in ("intro", "select_defender_intro", "combat_roll", "combat_result")
        )

        if not self.show_turn_overlay and not self.show_menu and not attack_overlay:
            self._draw_hud()

        if self.show_turn_overlay:
            self._draw_turn_overlay()
        elif self.show_menu:
            self.draw_menu()
        elif attack_overlay:
            subphase = self.attack_subphase
            if subphase == "intro":
                self._draw_attack_intro_overlay()
            elif subphase == "select_defender_intro":
                self._draw_attack_select_defender_overlay()
            elif subphase == "combat_roll":
                self._draw_combat_roll_overlay()
            elif subphase == "combat_result":
                self._draw_combat_result_overlay()

        pygame.display.flip()

    def _draw_hud(self):
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
            phase_text = "Phase: Truppen setzen"
            phase_surf = self.font_small.render(phase_text, True, (200, 200, 200))
            self.screen.blit(phase_surf, (panel_x + 18, panel_y + 38))

            remaining = player.reinforcements
            troop_label = self.font_small.render("Noch zu setzen:", True, (200, 200, 200))
            troop_num = self.font_large.render(str(remaining), True, (255, 230, 80))
            self.screen.blit(troop_label, (panel_x + 18, panel_y + 62))
            self.screen.blit(
                troop_num,
                (panel_x + panel_w - troop_num.get_width() - 15,
                 panel_y + panel_h // 2 - troop_num.get_height() // 2)
            )

        elif phase == "attack":
            subphase = self.attack_subphase
            if subphase == "select_attacker":
                phase_surf = self.font_small.render(
                    "Phase: Angriff – Angreifer wählen",
                    True,
                    (200, 200, 200)
                )
                self.screen.blit(phase_surf, (panel_x + 18, panel_y + 38))

                btn_w, btn_h = 320, 34
                btn_x = panel_x + 18
                btn_y = panel_y + panel_h + 10
                self.attack_end_phase_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
                mx, my = pygame.mouse.get_pos()
                hover = self.attack_end_phase_rect.collidepoint(mx, my)

                pygame.draw.rect(
                    self.screen,
                    (80, 100, 80) if hover else (55, 75, 55),
                    self.attack_end_phase_rect,
                    border_radius=6
                )
                end_txt = self.font_small.render(
                    "Zug beenden (Angriff überspringen)",
                    True,
                    (200, 230, 200)
                )
                self.screen.blit(
                    end_txt,
                    (btn_x + btn_w // 2 - end_txt.get_width() // 2,
                     btn_y + btn_h // 2 - end_txt.get_height() // 2)
                )

            elif subphase == "select_defender":
                phase_surf = self.font_small.render(
                    "Phase: Angriff – Ziel wählen",
                    True,
                    (200, 200, 200)
                )
                self.screen.blit(phase_surf, (panel_x + 18, panel_y + 38))
                if self.selected_attacker:
                    att_txt = self.font_small.render(
                        f"Angreifer: {self.selected_attacker.name.replace('_', ' ').title()}",
                        True,
                        (255, 230, 80)
                    )
                    self.screen.blit(att_txt, (panel_x + 18, panel_y + 62))
                self.attack_end_phase_rect = None
            else:
                self.attack_end_phase_rect = None

    def _draw_turn_overlay(self):
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

        header = self.font_small.render("DU BIST DRAN", True, (180, 180, 180))
        self.screen.blit(header, (card_x + card_w // 2 - header.get_width() // 2, card_y + 25))

        name_surf = self.font_large.render(player.name, True, player.color)
        self.screen.blit(name_surf, (card_x + card_w // 2 - name_surf.get_width() // 2, card_y + 60))

        reinf_text = f"Truppen zu setzen: {player.reinforcements}"
        reinf_surf = self.font.render(reinf_text, True, (255, 230, 80))
        self.screen.blit(
            reinf_surf,
            (card_x + card_w // 2 - reinf_surf.get_width() // 2, card_y + 140)
        )

        hint = self.font_small.render(
            "Klicke auf deine Länder um Truppen zu setzen",
            True,
            (160, 160, 160)
        )
        self.screen.blit(hint, (card_x + card_w // 2 - hint.get_width() // 2, card_y + 180))

        btn_w, btn_h = 200, 45
        btn_x = card_x + card_w // 2 - btn_w // 2
        btn_y = card_y + card_h - btn_h - 20

        self.turn_overlay_continue_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
        mx, my = pygame.mouse.get_pos()
        hover = self.turn_overlay_continue_rect.collidepoint(mx, my)
        btn_color = tuple(min(255, c + 50) for c in player.color) if hover else player.color

        pygame.draw.rect(self.screen, btn_color, self.turn_overlay_continue_rect, border_radius=8)
        btn_txt = self.font.render("Los geht's!", True, (255, 255, 255))
        self.screen.blit(
            btn_txt,
            (btn_x + btn_w // 2 - btn_txt.get_width() // 2,
             btn_y + btn_h // 2 - btn_txt.get_height() // 2)
        )

    def _draw_attack_intro_overlay(self):
        player = self.turn_manager.get_current_player()

        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))

        card_w, card_h = 560, 310
        card_x = WIDTH // 2 - card_w // 2
        card_y = HEIGHT // 2 - card_h // 2

        card = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
        card.fill((25, 10, 10, 240))
        self.screen.blit(card, (card_x, card_y))
        pygame.draw.rect(self.screen, (180, 40, 40), (card_x, card_y, card_w, 8))
        pygame.draw.rect(self.screen, (180, 40, 40), (card_x, card_y, card_w, card_h), 3)

        header = self.font_small.render("ANGRIFFSPHASE", True, (180, 100, 100))
        self.screen.blit(header, (card_x + card_w // 2 - header.get_width() // 2, card_y + 25))

        name_surf = self.font_large.render(player.name, True, player.color)
        self.screen.blit(name_surf, (card_x + card_w // 2 - name_surf.get_width() // 2, card_y + 58))

        pygame.draw.line(self.screen, (80, 40, 40), (card_x + 30, card_y + 120), (card_x + card_w - 30, card_y + 120), 1)

        hint1 = self.font.render("Waehle ein Territorium, das angreift", True, (230, 220, 220))
        self.screen.blit(hint1, (card_x + card_w // 2 - hint1.get_width() // 2, card_y + 138))

        hint2 = self.font_small.render("(mind. 2 Truppen erforderlich)", True, (150, 130, 130))
        self.screen.blit(hint2, (card_x + card_w // 2 - hint2.get_width() // 2, card_y + 175))

        btn_w, btn_h = 220, 48
        btn_x = card_x + card_w // 2 - btn_w // 2
        btn_y = card_y + card_h - btn_h - 20
        self.attack_intro_continue_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)

        mx, my = pygame.mouse.get_pos()
        hover = self.attack_intro_continue_rect.collidepoint(mx, my)
        btn_color = (220, 70, 70) if hover else (170, 35, 35)
        pygame.draw.rect(self.screen, btn_color, self.attack_intro_continue_rect, border_radius=10)

        btn_txt = self.font.render("Los geht's!", True, (255, 255, 255))
        self.screen.blit(btn_txt, (btn_x + btn_w // 2 - btn_txt.get_width() // 2,
                                   btn_y + btn_h // 2 - btn_txt.get_height() // 2))

    def _draw_attack_select_defender_overlay(self):
        player = self.turn_manager.get_current_player()
        attacker = self.selected_attacker

        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))

        card_w, card_h = 580, 310
        card_x = WIDTH // 2 - card_w // 2
        card_y = HEIGHT // 2 - card_h // 2

        card = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
        card.fill((25, 10, 10, 240))
        self.screen.blit(card, (card_x, card_y))
        pygame.draw.rect(self.screen, (180, 40, 40), (card_x, card_y, card_w, 8))
        pygame.draw.rect(self.screen, (180, 40, 40), (card_x, card_y, card_w, card_h), 3)

        header = self.font_small.render("ANGREIFER GEWAEHLT", True, (180, 100, 100))
        self.screen.blit(header, (card_x + card_w // 2 - header.get_width() // 2, card_y + 22))

        t_name = attacker.name.replace("_", " ").title()
        name_surf = self.font_large.render(t_name, True, player.color)
        self.screen.blit(name_surf, (card_x + card_w // 2 - name_surf.get_width() // 2, card_y + 55))

        troops_surf = self.font.render(f"{attacker.troops} Truppen verfuegbar", True, (255, 230, 80))
        self.screen.blit(troops_surf, (card_x + card_w // 2 - troops_surf.get_width() // 2, card_y + 115))

        pygame.draw.line(self.screen, (80, 40, 40), (card_x + 30, card_y + 148), (card_x + card_w - 30, card_y + 148), 1)

        hint = self.font.render("Waehle das Territorium, das du angreifen moechtest", True, (230, 220, 220))
        self.screen.blit(hint, (card_x + card_w // 2 - hint.get_width() // 2, card_y + 165))

        btn_w, btn_h = 220, 48
        btn_x = card_x + card_w // 2 - btn_w // 2
        btn_y = card_y + card_h - btn_h - 20
        self.attack_defender_intro_continue_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)

        mx, my = pygame.mouse.get_pos()
        hover = self.attack_defender_intro_continue_rect.collidepoint(mx, my)
        btn_color = (220, 70, 70) if hover else (170, 35, 35)
        pygame.draw.rect(self.screen, btn_color, self.attack_defender_intro_continue_rect, border_radius=10)

        btn_txt = self.font.render("Weiter", True, (255, 255, 255))
        self.screen.blit(btn_txt, (btn_x + btn_w // 2 - btn_txt.get_width() // 2,
                                   btn_y + btn_h // 2 - btn_txt.get_height() // 2))

    def _draw_combat_roll_overlay(self):
        combat = self.active_combat
        player = self.turn_manager.get_current_player()
        attacker = combat.attacking_territory
        defender = combat.defending_territory

        max_dice = min(Combat.MAX_ATTACKER_DICE, attacker.troops - 1)
        if self.pending_dice_count is None or self.pending_dice_count > max_dice:
            self.pending_dice_count = max_dice

        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))
        self.screen.blit(overlay, (0, 0))

        card_w, card_h = 720, 420
        card_x = WIDTH // 2 - card_w // 2
        card_y = HEIGHT // 2 - card_h // 2

        card = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
        card.fill((20, 12, 12, 245))
        self.screen.blit(card, (card_x, card_y))
        pygame.draw.rect(self.screen, (180, 40, 40), (card_x, card_y, card_w, 8))
        pygame.draw.rect(self.screen, (180, 40, 40), (card_x, card_y, card_w, card_h), 3)

        title = self.font_large.render("KAMPF!", True, (220, 60, 60))
        self.screen.blit(title, (card_x + card_w // 2 - title.get_width() // 2, card_y + 18))

        pygame.draw.line(self.screen, (80, 30, 30), (card_x + 30, card_y + 78), (card_x + card_w - 30, card_y + 78), 1)

        att_name = attacker.name.replace("_", " ").title()
        att_txt = self.font.render(att_name, True, player.color)
        self.screen.blit(att_txt, (card_x + 40, card_y + 90))

        att_num = self.font_large.render(str(attacker.troops), True, (255, 230, 80))
        self.screen.blit(att_num, (card_x + 40, card_y + 122))

        att_lbl = self.font_small.render("Truppen", True, (160, 140, 140))
        self.screen.blit(att_lbl, (card_x + 40 + att_num.get_width() + 8, card_y + 155))

        vs = self.font_large.render("VS", True, (160, 140, 140))
        self.screen.blit(vs, (card_x + card_w // 2 - vs.get_width() // 2, card_y + 130))

        def_player = self.players[defender.owner] if defender.owner is not None else None
        def_color = def_player.color if def_player else (200, 200, 200)
        def_name = defender.name.replace("_", " ").title()
        def_txt = self.font.render(def_name, True, def_color)
        self.screen.blit(def_txt, (card_x + card_w - 40 - def_txt.get_width(), card_y + 90))

        def_num = self.font_large.render(str(defender.troops), True, (255, 230, 80))
        self.screen.blit(def_num, (card_x + card_w - 40 - def_num.get_width(), card_y + 122))

        def_lbl = self.font_small.render("Truppen", True, (160, 140, 140))
        self.screen.blit(def_lbl, (card_x + card_w - 40 - def_num.get_width() - def_lbl.get_width() - 8, card_y + 155))

        pygame.draw.line(self.screen, (80, 30, 30), (card_x + 30, card_y + 205), (card_x + card_w - 30, card_y + 205), 1)

        dice_lbl = self.font_small.render("Wuerfelanzahl waehlen:", True, (200, 180, 180))
        self.screen.blit(dice_lbl, (card_x + card_w // 2 - dice_lbl.get_width() // 2, card_y + 218))

        self.combat_dice_rects = {}
        btn_w2, btn_h2 = 80, 46
        total_w = 3 * btn_w2 + 2 * 14
        start_x = card_x + card_w // 2 - total_w // 2

        for i in range(1, 4):
            bx = start_x + (i - 1) * (btn_w2 + 14)
            by = card_y + 248
            r = pygame.Rect(bx, by, btn_w2, btn_h2)
            self.combat_dice_rects[i] = r

            available = i <= max_dice
            selected = i == self.pending_dice_count

            if not available:
                bg = (45, 35, 35)
                fg = (90, 70, 70)
            elif selected:
                bg = (200, 50, 50)
                fg = (255, 255, 255)
            else:
                mx2, my2 = pygame.mouse.get_pos()
                hover = r.collidepoint(mx2, my2)
                bg = (100, 50, 50) if hover else (70, 35, 35)
                fg = (255, 255, 255)

            pygame.draw.rect(self.screen, bg, r, border_radius=8)
            if available:
                pygame.draw.rect(self.screen, (180, 40, 40) if selected else (120, 60, 60), r, 2, border_radius=8)

            d_txt = self.font_large.render(str(i), True, fg)
            self.screen.blit(d_txt, (bx + btn_w2 // 2 - d_txt.get_width() // 2,
                                     by + btn_h2 // 2 - d_txt.get_height() // 2))

        roll_w, roll_h = 280, 58
        roll_x = card_x + card_w // 2 - roll_w // 2
        roll_y = card_y + card_h - roll_h - 20
        self.combat_roll_rect = pygame.Rect(roll_x, roll_y, roll_w, roll_h)

        mx3, my3 = pygame.mouse.get_pos()
        hover_roll = self.combat_roll_rect.collidepoint(mx3, my3)
        roll_color = (230, 80, 80) if hover_roll else (180, 35, 35)
        pygame.draw.rect(self.screen, roll_color, self.combat_roll_rect, border_radius=12)
        pygame.draw.rect(self.screen, (220, 100, 100), self.combat_roll_rect, 2, border_radius=12)

        roll_txt = self.font_large.render("WUERFELN!", True, (255, 255, 255))
        self.screen.blit(roll_txt, (roll_x + roll_w // 2 - roll_txt.get_width() // 2,
                                    roll_y + roll_h // 2 - roll_txt.get_height() // 2))

    def _draw_combat_result_overlay(self):
        combat = self.active_combat
        player = self.turn_manager.get_current_player()
        attacker = combat.attacking_territory
        defender = combat.defending_territory
        def_player = self.players[defender.owner] if defender.owner is not None else None
        def_color = def_player.color if def_player else (200, 200, 200)

        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))
        self.screen.blit(overlay, (0, 0))

        card_w, card_h = 740, 500
        card_x = WIDTH // 2 - card_w // 2
        card_y = HEIGHT // 2 - card_h // 2

        card = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
        card.fill((20, 12, 12, 245))
        self.screen.blit(card, (card_x, card_y))
        pygame.draw.rect(self.screen, (180, 40, 40), (card_x, card_y, card_w, 8))
        pygame.draw.rect(self.screen, (180, 40, 40), (card_x, card_y, card_w, card_h), 3)

        title = self.font_large.render("WUERFELERGEBNIS", True, (220, 60, 60))
        self.screen.blit(title, (card_x + card_w // 2 - title.get_width() // 2, card_y + 18))

        pygame.draw.line(self.screen, (80, 30, 30), (card_x + 30, card_y + 78), (card_x + card_w - 30, card_y + 78), 1)

        att_label = self.font.render(attacker.name.replace("_", " ").title(), True, player.color)
        self.screen.blit(att_label, (card_x + 40, card_y + 90))

        att_dice = getattr(combat, "attacker_dice", [])
        for i, d in enumerate(att_dice):
            self._draw_die(card_x + 40 + i * 82, card_y + 125, d, (180, 40, 40))

        loss_att = getattr(combat, "last_attacker_losses", 0)
        loss_txt_a = self.font.render(
            f"Verluste: -{loss_att}",
            True,
            (255, 90, 90) if loss_att > 0 else (100, 180, 100)
        )
        self.screen.blit(loss_txt_a, (card_x + 40, card_y + 210))

        troops_att = self.font_small.render(f"Verbleibend: {attacker.troops} Truppen", True, (200, 200, 200))
        self.screen.blit(troops_att, (card_x + 40, card_y + 245))

        pygame.draw.line(self.screen, (80, 30, 30), (card_x + card_w // 2, card_y + 88), (card_x + card_w // 2, card_y + 275), 1)

        def_label = self.font.render(defender.name.replace("_", " ").title(), True, def_color)
        self.screen.blit(def_label, (card_x + card_w - 40 - def_label.get_width(), card_y + 90))

        def_dice = getattr(combat, "defender_dice", [])
        die_start_x = card_x + card_w - 40 - len(def_dice) * 82 + (82 - 60)
        for i, d in enumerate(def_dice):
            self._draw_die(die_start_x + i * 82, card_y + 125, d, (40, 80, 180))

        loss_def = getattr(combat, "last_defender_losses", 0)
        loss_txt_d = self.font.render(
            f"Verluste: -{loss_def}",
            True,
            (255, 90, 90) if loss_def > 0 else (100, 180, 100)
        )
        self.screen.blit(loss_txt_d, (card_x + card_w - 40 - loss_txt_d.get_width(), card_y + 210))

        troops_def = self.font_small.render(f"Verbleibend: {defender.troops} Truppen", True, (200, 200, 200))
        self.screen.blit(troops_def, (card_x + card_w - 40 - troops_def.get_width(), card_y + 245))

        pygame.draw.line(self.screen, (80, 30, 30), (card_x + 30, card_y + 285), (card_x + card_w - 30, card_y + 285), 1)

        if self.combat_last_conquered:
            status = self.font_large.render("TERRITORIUM EROBERT!", True, (255, 210, 50))
            self.screen.blit(status, (card_x + card_w // 2 - status.get_width() // 2, card_y + 305))
        elif not self.combat_last_can_continue:
            status = self.font.render("Zu wenig Truppen – Angriff wird abgebrochen.", True, (200, 150, 150))
            self.screen.blit(status, (card_x + card_w // 2 - status.get_width() // 2, card_y + 315))

        mx, my = pygame.mouse.get_pos()
        btn_h = 50

        if self.combat_last_conquered or not self.combat_last_can_continue:
            btn_w = 220
            btn_x = card_x + card_w // 2 - btn_w // 2
            btn_y = card_y + card_h - btn_h - 22
            self.combat_result_continue_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
            self.combat_result_end_rect = None

            hover = self.combat_result_continue_rect.collidepoint(mx, my)
            c = (200, 160, 30) if self.combat_last_conquered else (60, 80, 100)
            c_hover = (230, 190, 50) if self.combat_last_conquered else (80, 100, 130)
            pygame.draw.rect(self.screen, c_hover if hover else c, self.combat_result_continue_rect, border_radius=10)

            ok_txt = self.font.render("Weiter", True, (255, 255, 255))
            self.screen.blit(ok_txt, (btn_x + btn_w // 2 - ok_txt.get_width() // 2,
                                      btn_y + btn_h // 2 - ok_txt.get_height() // 2))
        else:
            btn_w = 240
            gap = 20
            total = btn_w * 2 + gap
            bx1 = card_x + card_w // 2 - total // 2
            bx2 = bx1 + btn_w + gap
            by = card_y + card_h - btn_h - 22

            self.combat_result_continue_rect = pygame.Rect(bx1, by, btn_w, btn_h)
            self.combat_result_end_rect = pygame.Rect(bx2, by, btn_w, btn_h)

            h1 = self.combat_result_continue_rect.collidepoint(mx, my)
            pygame.draw.rect(self.screen, (220, 70, 70) if h1 else (170, 35, 35), self.combat_result_continue_rect, border_radius=10)
            cont_txt = self.font.render("Weiterkaempfen", True, (255, 255, 255))
            self.screen.blit(cont_txt, (bx1 + btn_w // 2 - cont_txt.get_width() // 2,
                                        by + btn_h // 2 - cont_txt.get_height() // 2))

            h2 = self.combat_result_end_rect.collidepoint(mx, my)
            pygame.draw.rect(self.screen, (75, 85, 100) if h2 else (55, 65, 80), self.combat_result_end_rect, border_radius=10)
            end_txt = self.font.render("Angriff beenden", True, (200, 210, 220))
            self.screen.blit(end_txt, (bx2 + btn_w // 2 - end_txt.get_width() // 2,
                                       by + btn_h // 2 - end_txt.get_height() // 2))

    def _draw_die(self, x: int, y: int, value: int, color: tuple):
        size = 60
        pygame.draw.rect(self.screen, color, (x, y, size, size), border_radius=10)
        pygame.draw.rect(self.screen, (255, 255, 255), (x, y, size, size), 2, border_radius=10)
        num = self.font_large.render(str(value), True, (255, 255, 255))
        self.screen.blit(num, (x + size // 2 - num.get_width() // 2,
                               y + size // 2 - num.get_height() // 2))

    def run(self):
        clock = pygame.time.Clock()
        self.running = True

        while self.running:
            clock.tick(60)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if not self.show_turn_overlay:
                            self.show_menu = not self.show_menu

                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()

                    if self.show_turn_overlay:
                        if self.turn_overlay_continue_rect and self.turn_overlay_continue_rect.collidepoint(mouse_pos):
                            self.show_turn_overlay = False

                    elif self.show_menu:
                        self.handle_menu_click(mouse_pos)

                    elif (
                        self.turn_manager.phase == "attack" and
                        self.attack_subphase in ("intro", "select_defender_intro", "combat_roll", "combat_result")
                    ):
                        self._handle_attack_overlay_click(mouse_pos)

                    else:
                        self.handle_click(mouse_pos)

            self.draw()

        pygame.quit()
        sys.exit()

    def draw_menu(self):
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        title = self.font.render("MENUE", True, (255, 255, 255))
        self.screen.blit(title, (WIDTH // 2 - 50, HEIGHT // 2 - 150))

        self.resume_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 - 20, 200, 40)
        self.quit_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 40, 200, 40)

        pygame.draw.rect(self.screen, (80, 80, 80), self.resume_rect)
        pygame.draw.rect(self.screen, (120, 50, 50), self.quit_rect)

        resume = self.font.render("Weiter", True, (255, 255, 255))
        quit_game = self.font.render("Beenden", True, (255, 255, 255))

        self.screen.blit(resume, (self.resume_rect.x + 40, self.resume_rect.y + 5))
        self.screen.blit(quit_game, (self.quit_rect.x + 40, self.quit_rect.y + 5))

    def handle_menu_click(self, pos):
        if self.resume_rect and self.resume_rect.collidepoint(pos):
            self.show_menu = False
        if self.quit_rect and self.quit_rect.collidepoint(pos):
            print("Spiel wird beendet...")
            self.running = False