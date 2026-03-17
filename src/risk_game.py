import pygame
import sys
import xml.etree.ElementTree as ET
from svgpathtools import parse_path

pygame.init()

WIDTH = 1920
HEIGHT = 1080
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Risk Map")

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

# Nur die 42 Risiko-Territorien
TERRITORY_IDS = [
    "eastern_australia", "indonesia", "alaska", "new_guinea",
    "ontario", "northwest_territory", "venezuela", "madagascar",
    "north_africa", "greenland", "iceland", "great_britain",
    "scandinavia", "japan", "yakursk", "kamchatka", "siberia",
    "ural", "afghanistan", "middle_east", "india", "siam",
    "china", "mongolia", "irkutsk", "ukraine", "southern_europe",
    "western_europe", "northern_europe", "egypt", "east_africa",
    "congo", "south_africa", "brazil", "argentina",
    "eastern_united_states", "western_united_states", "quebec",
    "central_america", "peru", "western_australia", "alberta"
]

# Kontinentfarben
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

# SVG parsen – nur countries layer
tree = ET.parse("risk_map.svg")
root = tree.getroot()
ns = {"svg": "http://www.w3.org/2000/svg"}

territories = []

for elem in root.iter("{http://www.w3.org/2000/svg}path"):
    tid = elem.get("id", "")
    if tid not in TERRITORY_IDS:
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
        sx, sy = svg_to_screen(x, y)
        points.append((sx, sy))

    if len(points) < 3:
        continue

    territories.append({
        "id":      tid,
        "points":  points,
        "color":   CONTINENT_COLORS.get(tid, (180, 180, 180)),
        "glow":    0.0,
        "glowing": False
    })

print(f"Länder geladen: {len(territories)}")

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

def blend_color(base, glow_color, t):
    r = int(base[0] + (glow_color[0] - base[0]) * t)
    g = int(base[1] + (glow_color[1] - base[1]) * t)
    b = int(base[2] + (glow_color[2] - base[2]) * t)
    return (max(0, min(255, r)),
            max(0, min(255, g)),
            max(0, min(255, b)))

def draw_glow(surface, points, color, t, layers=8):
    cx = sum(p[0] for p in points) / len(points)
    cy = sum(p[1] for p in points) / len(points)

    for i in range(layers, 0, -1):
        alpha = int(80 * t * (i / layers))
        scale = 1 + i * 0.005

        scaled = [
            (cx + (px - cx) * scale, cy + (py - cy) * scale)
            for px, py in points
        ]
        valid = [(x, y) for x, y in scaled
                 if -200 <= x <= WIDTH + 200 and -200 <= y <= HEIGHT + 200]

        if len(valid) < 3:
            continue

        glow_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.polygon(
            glow_surf,
            (color[0], color[1], color[2], alpha),
            valid, 0
        )
        surface.blit(glow_surf, (0, 0))

font = pygame.font.SysFont("Arial", 22, bold=True)
clock = pygame.time.Clock()

GLOW_COLOR = (255, 255, 150)
GLOW_SPEED = 0.06
GLOW_DECAY = 0.025

selected = None
running = True

while running:
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse = pygame.mouse.get_pos()
            for t in territories:
                if point_in_polygon(mouse, t["points"]):
                    t["glowing"] = True
                    t["glow"] = 0.0
                    selected = t
                    print(f"Angeklickt: {t['id']}")

    # Glow updaten
    for t in territories:
        if t["glowing"]:
            t["glow"] = min(1.0, t["glow"] + GLOW_SPEED)
            if t["glow"] >= 1.0:
                t["glowing"] = False
        else:
            t["glow"] = max(0.0, t["glow"] - GLOW_DECAY)

    screen.fill((30, 100, 160))

    # Länder zeichnen
    for t in territories:
        valid = [(x, y) for x, y in t["points"]
                 if 0 <= x <= WIDTH and 0 <= y <= HEIGHT]
        if len(valid) < 3:
            continue

        color = blend_color(t["color"], GLOW_COLOR, t["glow"])
        try:
            pygame.draw.polygon(screen, color, valid, 0)
            pygame.draw.polygon(screen, (30, 30, 30), valid, 1)
        except Exception:
            pass

    # Glow drüber
    for t in territories:
        if t["glow"] > 0.01:
            valid = [(x, y) for x, y in t["points"]
                     if -200 <= x <= WIDTH + 200 and -200 <= y <= HEIGHT + 200]
            if len(valid) < 3:
                continue
            try:
                draw_glow(screen, valid, GLOW_COLOR, t["glow"])
            except Exception:
                pass

    # Name anzeigen
    if selected:
        name = selected["id"].replace("_", " ").title()
        shadow = font.render(name, True, (0, 0, 0))
        text   = font.render(name, True, (255, 255, 255))
        screen.blit(shadow, (12, 12))
        screen.blit(text,   (10, 10))

    pygame.display.flip()

pygame.quit()
sys.exit()