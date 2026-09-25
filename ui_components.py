import pygame

class Button:
    def __init__(self, x, y, width, height, text, color, hover_color, text_color=(255, 255, 255), font_size=18):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.font = pygame.font.SysFont("Arial", font_size)

    def draw(self, surface):
        mouse_pos = pygame.mouse.get_pos()
        current_color = self.hover_color if self.rect.collidepoint(mouse_pos) else self.color
        pygame.draw.rect(surface, current_color, self.rect, border_radius=6)
        
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def is_clicked(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(event.pos)
        return False


class TextInput:
    def __init__(self, x, y, width, height, placeholder=""):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = ""
        self.placeholder = placeholder
        self.active = False
        self.font = pygame.font.SysFont("Arial", 16)
        self.color_inactive = (200, 205, 210)
        self.color_active = (41, 128, 185)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key != pygame.K_RETURN:
                self.text += event.unicode

    def draw(self, surface):
        color = self.color_active if self.active else self.color_inactive
        pygame.draw.rect(surface, (255, 255, 255), self.rect, border_radius=4)
        pygame.draw.rect(surface, color, self.rect, 2, border_radius=4)
        
        if not self.text and not self.active:
            txt_surface = self.font.render(self.placeholder, True, (150, 150, 150))
        else:
            txt_surface = self.font.render(self.text, True, (44, 62, 80))
            
        surface.blit(txt_surface, (self.rect.x + 8, self.rect.y + 8))

    def clear(self):
        self.text = ""