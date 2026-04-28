import pygame

PLAYER_COLORS = [
    (220, 60,  60),   # Rot
    (60,  100, 220),  # Blau
    (60,  200, 80),   # Grün
    (0,   0,   0),    # Schwarz
    (180, 60,  220),  # Lila
]


def run_player_select() -> int:
    pygame.init()
    screen = pygame.display.set_mode((400, 300))
    pygame.display.set_caption("Spieleranzahl wählen")
    font_big = pygame.font.SysFont("Arial", 28, bold=True)
    font_btn = pygame.font.SysFont("Arial", 32, bold=True)

    buttons = [
        (n, pygame.Rect(50 + i * 75, 140, 60, 60))
        for i, n in enumerate(range(2, 6))
    ]

    selected = None
    while selected is None:
        screen.fill((30, 30, 40))

        label = font_big.render("Wie viele Spieler?", True, (255, 255, 255))
        screen.blit(label, (200 - label.get_width() // 2, 60))

        mx, my = pygame.mouse.get_pos()
        for n, rect in buttons:
            color = PLAYER_COLORS[n - 2]
            bg = tuple(min(255, c + 40) for c in color) if rect.collidepoint(mx, my) else color
            pygame.draw.rect(screen, bg, rect, border_radius=10)
            txt = font_btn.render(str(n), True, (255, 255, 255))
            screen.blit(txt, (rect.centerx - txt.get_width() // 2,
                               rect.centery - txt.get_height() // 2))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if event.type == pygame.MOUSEBUTTONDOWN:
                for n, rect in buttons:
                    if rect.collidepoint(event.pos):
                        selected = n

        pygame.display.flip()

    return selected