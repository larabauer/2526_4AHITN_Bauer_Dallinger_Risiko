import pygame

WIDTH = 1920
HEIGHT = 1080

SVG_WIDTH = 749.81909
SVG_HEIGHT = 519.06781
OFFSET_X = -167.99651
OFFSET_Y = -118.55507

SCALE_X = WIDTH / SVG_WIDTH
SCALE_Y = HEIGHT / SVG_HEIGHT


def svg_to_screen(x: float, y: float) -> tuple[float, float]:
    return (x + OFFSET_X) * SCALE_X, (y + OFFSET_Y) * SCALE_Y


def point_in_polygon(point: tuple, polygon: list) -> bool:
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
    def __init__(self, name: str, points: list, color: tuple):
        self.name = name
        self.points = points
        self.color = color
        self.border_color = (30, 30, 30)
        self.owner: int | None = None
        self.troops: int = 1

        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        self.center = ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)

    def set_owner(self, player_index: int, player_colors: list) -> None:
        self.owner = player_index
        self.border_color = player_colors[player_index]

    def contains(self, point: tuple) -> bool:
        return point_in_polygon(point, self.points)

    def draw(self, screen, font) -> None:
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
        text   = font.render(str(self.troops), True, num_color)
        screen.blit(shadow, (cx - shadow.get_width() // 2 + 1, cy - shadow.get_height() // 2 + 1))
        screen.blit(text,   (cx - text.get_width()   // 2,     cy - text.get_height()   // 2))