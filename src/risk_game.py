import  pygame
import sys

pygame.init()

screen = pygame.display.set_mode((1000, 600))
pygame.display.set_caption("Risk Game")

running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((40, 120, 40))  # Hintergrund

    pygame.draw.rect(screen, (200, 200, 200), (100, 100, 150, 100))
    pygame.draw.rect(screen, (200, 200, 200), (300, 150, 150, 100))
    pygame.draw.rect(screen, (200, 200, 200), (500, 250, 150, 100))

    mouse_pos = pygame.mouse.get_pos()

    pygame.display.update()

pygame.quit()
sys.exit()