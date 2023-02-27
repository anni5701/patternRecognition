import random

import kivy

kivy.require("2.1.0")

from kivy.app import App
from kivy.logger import Logger
from kivy.uix.widget import Widget
from kivy.graphics import Color, Ellipse, Line


# https://kivy.org/doc/stable/tutorials/firstwidget.html
# https://kivy-fork.readthedocs.io/en/latest/api-kivy.core.window.html


class MyWidget(Widget):
    def on_motion(self, me):
        Logger.warn("Pen: " + str(me))

    def on_touch_down(self, touch):
        Logger.info("Pen: " + str(touch))

        with self.canvas:
            Color(random.random(), random.random(), random.random())

            radius = 10.0
            Ellipse(
                pos=(touch.x - radius, touch.y - radius), size=(radius * 2, radius * 2)
            )

            touch.ud["line"] = Line(points=(touch.x, touch.y))

    def on_touch_move(self, touch):
        Logger.info("Pen: " + str(touch))

        touch.ud["line"].points += [touch.x, touch.y]

    def on_touch_up(self, touch):
        Logger.info("Pen: " + str(touch))


class MyApp(App):
    def build(self):
        return MyWidget()


if __name__ == "__main__":
    MyApp().run()
