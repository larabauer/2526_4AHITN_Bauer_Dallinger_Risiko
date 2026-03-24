import pygame

PLAYER_COLORS = [
    (220, 60,  60),   # Rot
    (60,  100, 220),  # Blau
    (60,  200, 80),   # Grün
    (220, 180, 40),   # Gelb
    (180, 60,  220),  # Lila
]

def run_player_select():
    pygame.init()
    screen = pygame.display.set_mode((400, 300))
    pygame.display.set_caption("Spieleranzahl wählen")
    font_big  = pygame.font.SysFont("Arial", 28, bold=True)
    font_btn  = pygame.font.SysFont("Arial", 32, bold=True)

    buttons = []
    for i, n in enumerate(range(2, 6)):
        rect = pygame.Rect(50 + i * 75, 140, 60, 60)
        buttons.append((n, rect))

    selected = None
    while selected is None:
        screen.fill((30, 30, 40))
        label = font_big.render("Wie viele Spieler?", True, (255, 255, 255))
        screen.blit(label, (400 // 2 - label.get_width() // 2, 60))

        mx, my = pygame.mouse.get_pos()
        for n, rect in buttons:
            hover = rect.collidepoint(mx, my)
            color = PLAYER_COLORS[n - 2]
            bg    = tuple(min(255, c + 40) for c in color) if hover else color
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