import pygame
import sys
import xml.etree.ElementTree as ET
from svgpathtools import parse_path
import initialCountries
from player_select import PLAYER_COLORS
from player import Player
from turn_manager import TurnManager

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
        self.id           = tid
        self.points       = points
        self.color        = color
        self.border_color = (30, 30, 30)
        self.owner        = None
        self.troops       = 1

        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        self.center = (
            (min(xs) + max(xs)) / 2,
            (min(ys) + max(ys)) / 2
        )

    def set_owner(self, player_index, player_colors):
        self.owner        = player_index
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
        text   = font.render(str(self.troops), True, num_color)
        screen.blit(shadow, (cx - shadow.get_width() // 2 + 1,
                              cy - shadow.get_height() // 2 + 1))
        screen.blit(text,   (cx - text.get_width() // 2,
                              cy - text.get_height() // 2))


class MapLoader:
    CONTINENT_COLORS = {
        "eastern_australia": (200, 100, 50),
        "western_australia": (200, 100, 50),
        "new_guinea":        (200, 100, 50),
        "indonesia":         (200, 100, 50),
        "alaska":            (100, 180, 100),
        "ontario":           (100, 180, 100),
        "northwest_territory":(100, 180, 100),
        "quebec":            (100, 180, 100),
        "eastern_united_states":(100, 180, 100),
        "western_united_states":(100, 180, 100),
        "central_america":   (100, 180, 100),
        "alberta":           (100, 180, 100),
        "greenland":         (100, 180, 100),
        "venezuela":         (220, 180, 50),
        "brazil":            (220, 180, 50),
        "peru":              (220, 180, 50),
        "argentina":         (220, 180, 50),
        "iceland":           (150, 200, 220),
        "great_britain":     (150, 200, 220),
        "scandinavia":       (150, 200, 220),
        "northern_europe":   (150, 200, 220),
        "western_europe":    (150, 200, 220),
        "southern_europe":   (150, 200, 220),
        "ukraine":           (150, 200, 220),
        "north_africa":      (220, 160, 80),
        "egypt":             (220, 160, 80),
        "east_africa":       (220, 160, 80),
        "congo":             (220, 160, 80),
        "south_africa":      (220, 160, 80),
        "madagascar":        (220, 160, 80),
        "ural":              (180, 120, 200),
        "siberia":           (180, 120, 200),
        "yakursk":           (180, 120, 200),
        "kamchatka":         (180, 120, 200),
        "irkutsk":           (180, 120, 200),
        "mongolia":          (180, 120, 200),
        "china":             (180, 120, 200),
        "afghanistan":       (180, 120, 200),
        "middle_east":       (180, 120, 200),
        "india":             (180, 120, 200),
        "siam":              (180, 120, 200),
        "japan":             (180, 120, 200),
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
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Risk Map")

        self.font          = pygame.font.SysFont("Arial", 22, bold=True)
        self.territories   = MapLoader.load_territories()
        self.num_players   = num_players
        self.player_colors = PLAYER_COLORS[:num_players]
        self.selected      = None

        self.players = [
            Player(f"Player {i + 1}", self.player_colors[i])
            for i in range(num_players)
        ]
        print(self.players) # Print, um die player zu sehen

        self.turn_manager = TurnManager(self.players)

        self._assign_territories()

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

    def handle_click(self, pos):
        for t in self.territories:
            if t.contains(pos):
                self.selected = t
                print(f"Angeklickt: {t.id}")

    def draw(self):
        self.screen.fill((30, 100, 160))

        for t in self.territories:
            t.draw(self.screen, self.font)

        if self.selected:
            name   = self.selected.id.replace("_", " ").title()
            shadow = self.font.render(name, True, (0, 0, 0))
            text   = self.font.render(name, True, (255, 255, 255))
            self.screen.blit(shadow, (12, 12))
            self.screen.blit(text,   (10, 10))

        pygame.display.flip()

    def run(self):
        clock   = pygame.time.Clock()
        running = True

        while running:
            clock.tick(60)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_click(pygame.mouse.get_pos())

            self.draw()

        pygame.quit()
        sys.exit()