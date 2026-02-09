"""Custom UI components for the YouTube Downloader app."""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle
from kivy.properties import NumericProperty


class StyledBoxLayout(BoxLayout):
    """Custom BoxLayout with rounded background"""

    def __init__(self, bg_color=(0.15, 0.15, 0.2, 1), corner_radius=15, **kwargs):
        super().__init__(**kwargs)
        self.bg_color = bg_color
        self.corner_radius = corner_radius
        with self.canvas.before:
            Color(*self.bg_color)
            self.rect = RoundedRectangle(
                pos=self.pos, size=self.size, radius=[self.corner_radius]
            )
        self.bind(pos=self._update_rect, size=self._update_rect)

    def _update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size


class StyledProgressBar(Widget):
    """Custom progress bar with gradient styling"""

    progress = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self._update, size=self._update, progress=self._update)
        self._update()

    def _update(self, *args):
        self.canvas.clear()
        with self.canvas:
            # Background
            Color(0.2, 0.2, 0.28, 1)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[10])
            # Progress fill
            if self.progress > 0:
                Color(0.4, 0.6, 1, 1)  # Bright blue
                fill_width = (self.width - 4) * (self.progress / 100)
                RoundedRectangle(
                    pos=(self.x + 2, self.y + 2),
                    size=(fill_width, self.height - 4),
                    radius=[8],
                )


class GradientButton(Button):
    """Custom Button with gradient-like styling"""

    def __init__(self, gradient_colors=None, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_color = (0, 0, 0, 0)  # Transparent default
        self.colors = gradient_colors or [(0.4, 0.2, 0.8, 1), (0.2, 0.6, 0.8, 1)]

        with self.canvas.before:
            Color(*self.colors[0])
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[12])
        self.bind(pos=self._update_rect, size=self._update_rect)

    def _update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
