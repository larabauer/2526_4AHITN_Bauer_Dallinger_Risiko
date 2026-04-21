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
    return (sx, sy)


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
    def __init__(self, tid, points, color):
        self.id = tid
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
        valid = [(x, y) for x, y in self.points
                 if 0 <= x <= WIDTH and 0 <= y <= HEIGHT]
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
        screen.blit(shadow, (cx - shadow.get_width() // 2 + 1,
                             cy - shadow.get_height() // 2 + 1))
        screen.blit(text, (cx - text.get_width() // 2,
                           cy - text.get_height() // 2))


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
        "yakursk": (180, 120, 200),
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

        territory_ids = initialCountries.get_countries_from_json()
        territories = []

        for elem in root.iter("{http://www.w3.org/2000/svg}path"):
            tid = elem.get("id", "")
            if tid not in territory_ids:
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

            color = MapLoader.CONTINENT_COLORS.get(tid, (180, 180, 180))
            territories.append(Territory(tid, points, color))

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

    def _assign_territories(self):
        assignments = initialCountries.initial_countries_for_players(self.num_players)
        id_to_territory = {t.id: t for t in self.territories}

        for player_index, country_ids in enumerate(assignments):
            player = self.players[player_index]
            for cid in country_ids:
                if cid in id_to_territory:
                    territory = id_to_territory[cid]
                    territory.set_owner(player_index, self.player_colors)
                    player.add_territory(territory)

    def _start_placement_phase(self):
        player = self.turn_manager.get_current_player()
        player.calculate_reinforcements(self.continents_data)
        self.turn_manager.set_phase("placement")
        self.show_turn_overlay = True

    def _start_attack_phase(self):
        player = self.turn_manager.get_current_player()
        self.turn_manager.set_phase("attack")

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
                            print(f"+1 Truppe auf {t.id} | Noch zu setzen: {current_player.reinforcements}")

                            if current_player.reinforcements == 0:
                                self._start_attack_phase()
                                self._end_turn()
                    else:
                        print("Das ist nicht dein Land!")
                    self.selected = t
                    break
        elif phase == "attack":
            for t in self.territories:
                if t.contains(pos):
                    if t.owner != current_index:
                        break

    def _end_turn(self):
        self.turn_manager.next_player()
        self._start_placement_phase()

    # ── Zeichnen ──────────────────────────────────────────────────────────────

    def draw(self):
        self.screen.fill((30, 100, 160))

        for t in self.territories:
            t.draw(self.screen, self.font)

        if self.selected:
            name = self.selected.id.replace("_", " ").title()
            shadow = self.font.render(name, True, (0, 0, 0))
            text = self.font.render(name, True, (255, 255, 255))
            self.screen.blit(shadow, (12, 12))
            self.screen.blit(text, (10, 10))

        if not self.show_turn_overlay and not self.show_menu:
            self._draw_hud()

        if self.show_turn_overlay:
            self._draw_turn_overlay()

        if self.show_menu:
            self.draw_menu()

        pygame.display.flip()

    def _draw_hud(self):
        player = self.turn_manager.get_current_player()
        phase = self.turn_manager.phase

        panel_w, panel_h = 340, 90
        panel_x = WIDTH - panel_w - 20
        panel_y = 20

        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 160))
        self.screen.blit(panel, (panel_x, panel_y))

        pygame.draw.rect(self.screen, player.color,
                         (panel_x, panel_y, 8, panel_h))

        name_surf = self.font.render(player.name, True, player.color)
        self.screen.blit(name_surf, (panel_x + 18, panel_y + 10))

        phase_text = "Phase: Truppen setzen" if phase == "placement" else f"Phase: {phase}"
        phase_surf = self.font_small.render(phase_text, True, (200, 200, 200))
        self.screen.blit(phase_surf, (panel_x + 18, panel_y + 38))

        remaining = player.reinforcements
        troop_label = self.font_small.render("Noch zu setzen:", True, (200, 200, 200))
        troop_num = self.font_large.render(str(remaining), True, (255, 230, 80))
        self.screen.blit(troop_label, (panel_x + 18, panel_y + 58))
        self.screen.blit(troop_num,
                         (panel_x + panel_w - troop_num.get_width() - 15,
                          panel_y + panel_h // 2 - troop_num.get_height() // 2))

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

        pygame.draw.rect(self.screen, player.color,
                         (card_x, card_y, card_w, 8))
        pygame.draw.rect(self.screen, player.color,
                         (card_x, card_y, card_w, card_h), 3)

        header = self.font_small.render("DU BIST DRAN", True, (180, 180, 180))
        self.screen.blit(header,
                         (card_x + card_w // 2 - header.get_width() // 2,
                          card_y + 25))

        name_surf = self.font_large.render(player.name, True, player.color)
        self.screen.blit(name_surf,
                         (card_x + card_w // 2 - name_surf.get_width() // 2,
                          card_y + 60))

        reinf_text = f"Truppen zu setzen: {player.reinforcements}"
        reinf_surf = self.font.render(reinf_text, True, (255, 230, 80))
        self.screen.blit(reinf_surf,
                         (card_x + card_w // 2 - reinf_surf.get_width() // 2,
                          card_y + 140))

        hint = self.font_small.render("Klicke auf deine Länder um Truppen zu setzen", True, (160, 160, 160))
        self.screen.blit(hint,
                         (card_x + card_w // 2 - hint.get_width() // 2,
                          card_y + 180))

        btn_w, btn_h = 200, 45
        btn_x = card_x + card_w // 2 - btn_w // 2
        btn_y = card_y + card_h - btn_h - 20

        self.turn_overlay_continue_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)

        mx, my = pygame.mouse.get_pos()
        hover = self.turn_overlay_continue_rect.collidepoint(mx, my)
        btn_color = tuple(min(255, c + 50) for c in player.color) if hover else player.color

        pygame.draw.rect(self.screen, btn_color,
                         self.turn_overlay_continue_rect, border_radius=8)
        btn_txt = self.font.render("Los geht's!", True, (255, 255, 255))
        self.screen.blit(btn_txt,
                         (btn_x + btn_w // 2 - btn_txt.get_width() // 2,
                          btn_y + btn_h // 2 - btn_txt.get_height() // 2))

    # ── Event-Handling ────────────────────────────────────────────────────────

    def run(self):
        clock = pygame.time.Clock()
        self.running = True

        while self.running:
            clock.tick(60)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                # ESC nur verarbeiten wenn kein Overlay offen ist
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if not self.show_turn_overlay:       # ← NEU: Overlay blockt ESC
                            self.show_menu = not self.show_menu

                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()

                    if self.show_turn_overlay:
                        # Nur Weiter-Button reagiert, alles andere ignoriert
                        if (self.turn_overlay_continue_rect and
                                self.turn_overlay_continue_rect.collidepoint(mouse_pos)):
                            self.show_turn_overlay = False

                    elif self.show_menu:
                        # Nur Menü-Buttons reagieren, Karte wird ignoriert
                        self.handle_menu_click(mouse_pos)

                    else:
                        # Normales Spiel
                        self.handle_click(mouse_pos)

            self.draw()

        pygame.quit()
        sys.exit()

    # ── Menü ──────────────────────────────────────────────────────────────────

    def draw_menu(self):
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        title = self.font.render("MENÜ", True, (255, 255, 255))
        self.screen.blit(title, (WIDTH // 2 - 50, HEIGHT // 2 - 150))

        self.resume_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 - 20, 200, 40)
        self.quit_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 40, 200, 40)

        pygame.draw.rect(self.screen, (80, 80, 80), self.resume_rect)
        pygame.draw.rect(self.screen, (120, 50, 50), self.quit_rect)

        resume = self.font.render("Weiter", True, (255, 255, 255))
        quit_game = self.font.render("Beenden", True, (255, 255, 255))

        self.screen.blit(resume,
                         (self.resume_rect.x + 40, self.resume_rect.y + 5))
        self.screen.blit(quit_game,
                         (self.quit_rect.x + 40, self.quit_rect.y + 5))

    def handle_menu_click(self, pos):
        if self.resume_rect and self.resume_rect.collidepoint(pos):
            self.show_menu = False
        if self.quit_rect and self.quit_rect.collidepoint(pos):
            print("Spiel wird beendet...")
            self.running = False