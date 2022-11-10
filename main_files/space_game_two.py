#!/usr/bin/env python3

import os
import contextlib
import math
import random

from superwires import color, games
from settings import Config

MEDIA_PATH = "./media"
games.init(Config.WIDTH, Config.HEIGHT, Config.FPS)


class Wrapper(games.Sprite):
    def update(self):
        if self.top > games.screen.height:
            self.bottom = 0
        if self.bottom < 0:
            self.top = games.screen.height
        if self.left > games.screen.width:
            self.right = 0
        if self.right < 0:
            self.left = games.screen.width

    def die(self):
        self.destroy()


class Collider(Wrapper):
    def update(self):
        super().update()
        if self.overlapping_sprites:
            for sprite in self.overlapping_sprites:
                sprite.die()
            self.die()

    def die(self):
        new_expl = Explosion(x=self.x, y=self.y)
        games.screen.add(new_expl)
        self.destroy()


class Asteroid(Wrapper):


    SMALL = 1
    MIDDLE = 2
    LARGE = 3
    SPEED = 2
    SPAWN = 2
    POINTS = 30

    images = {
        SMALL: games.load_image(os.path.join(MEDIA_PATH, "astr_sml.png")),
        MIDDLE: games.load_image(os.path.join(MEDIA_PATH, "astr_mdl.png")),
        LARGE: games.load_image(os.path.join(MEDIA_PATH, "astr_lrg.png")),
    }

    total = 0

    def __init__(self, game, x, y, size):
        super().__init__(
            image=Asteroid.images[size],
            x=x,
            y=y,
            dx=random.choice([1, -1]) * Asteroid.SPEED * random.random() / size,
            dy=random.choice([1, -1]) * Asteroid.SPEED * random.random() / size,
        )
        self.size = size
        self.game = game
        Asteroid.total += 1

    def die(self):
        Asteroid.total -= 1
        self.game.score.value += int(Asteroid.POINTS / self.size)
        if self.size != Asteroid.SMALL:
            for _ in range(Asteroid.SPAWN):
                new_asteroid = Asteroid(
                    game=self.game, x=self.x, y=self.y, size=self.size - 1
                )
                games.screen.add(new_asteroid)
        super().die()
        if Asteroid.total == 0:
            self.game.advance()


class Ship(Collider):
    image = games.load_image(os.path.join(MEDIA_PATH, "ship2.png"))
    sound = games.load_sound(os.path.join(MEDIA_PATH, "missle.wav"))

    ROT_STEP = 3
    MOV_STEP = 3
    MSL_DELAY = 25
    VELOCITY_MAX = 3

    def __init__(self, game, x, y):
        super().__init__(image=self.image, x=x, y=y)
        self.game = game
        self.missle_wait = 0

    def update(self):
        super().update()
        self.dx = min(max(self.dx, -self.VELOCITY_MAX), self.VELOCITY_MAX)
        self.dy = min(max(self.dy, -self.VELOCITY_MAX), self.VELOCITY_MAX)

        if games.keyboard.is_pressed(games.K_w):
            self.y -= 1
        if games.keyboard.is_pressed(games.K_s):
            self.y += 1
        if games.keyboard.is_pressed(games.K_a):
            self.x -= 1
        if games.keyboard.is_pressed(games.K_d):
            self.x += 1
        if games.keyboard.is_pressed(games.K_RIGHT):
            self.angle += self.ROT_STEP
        if games.keyboard.is_pressed(games.K_LEFT):
            self.angle -= self.ROT_STEP
        if games.keyboard.is_pressed(games.K_UP):
            self.sound.play()
            angle = self.angle * math.pi / 180
            self.dx = self.MOV_STEP * math.sin(angle)
            self.dy = self.MOV_STEP * -math.cos(angle)
        if games.keyboard.is_pressed(games.K_1):
            self.angle = 0
        if games.keyboard.is_pressed(games.K_2):
            self.angle = 180
        if games.keyboard.is_pressed(games.K_q):
            self.game.end()

        # draw new fired rocket
        if self.missle_wait > 0:
            self.missle_wait -= 1
        if games.keyboard.is_pressed(games.K_SPACE) and self.missle_wait == 0:
            new_missle = Missle(self.x, self.y, self.angle)
            games.screen.add(new_missle)
            self.missle_wait = self.MSL_DELAY

    def die(self):
        self.game.end()
        super().die()


class Missle(Collider):

    image = games.load_image(os.path.join(MEDIA_PATH, "msl.png"))
    sound = games.load_sound(os.path.join(MEDIA_PATH, "missle.wav"))
    BUFFER = 90  # distance to starship
    VEL_FACTOR = 7  # rocket velocity
    LIFETIME = 40

    def __init__(self, ship_x, ship_y, ship_angle):
        Missle.sound.play()
        angle = ship_angle * math.pi / 180
        buffer_x = Missle.BUFFER * math.sin(angle)
        buffer_y = Missle.BUFFER * -math.cos(angle)
        x = ship_x + buffer_x
        y = ship_y + buffer_y
        dx = Missle.VEL_FACTOR * math.sin(angle)
        dy = Missle.VEL_FACTOR * -math.cos(angle)
        super().__init__(image=Missle.image, x=x, y=y, dx=dx, dy=dy)

        self.lifetime = Missle.LIFETIME

    def update(self):
        super().update()
        self.lifetime -= 1
        if self.lifetime == 0:
            self.destroy()


class Explosion(games.Animation):
    sound = games.load_sound(os.path.join(MEDIA_PATH, "explosion3.wav"))

    raw_images = ["expl1.png", "expl2.png", "expl3.png", "expl4.png"]
    images = [os.path.join(MEDIA_PATH, r) for r in raw_images]

    def __init__(self, x, y):
        super().__init__(
            images=Explosion.images,
            x=x,
            y=y,
            n_repeats=1,
            repeat_interval=7,
            is_collideable=False,
        )
        Explosion.sound.play()


class Game:
    BUFFER = 150

    def __init__(self):
        self.level = 0
        self.sound = games.load_sound(os.path.join(MEDIA_PATH, "missle.wav"))
        self.score = games.Text(
            value=0,
            size=30,
            color=color.white,
            top=5,
            right=games.screen.width - 10,
            is_collideable=False,
        )
        games.screen.add(self.score)

        self.ship = Ship(
            game=self,
            x=games.screen.width / 2,
            y=games.screen.height / 2)
        games.screen.add(self.ship)

    def play(self):
        games.music.load(os.path.join(MEDIA_PATH, "theme.mid"))
        games.music.play(-1)

        space_img = games.load_image(
            os.path.join(MEDIA_PATH, "space.jpg"), transparent=False)
        games.screen.background = space_img

        self.advance()
        games.screen.mainloop()

    def advance(self):
        self.level += 1
        for _ in range(self.level):
            x_min = random.randrange(self.BUFFER)
            y_min = self.BUFFER - x_min
            x_distance = random.randrange(x_min, games.screen.width - x_min)
            y_distance = random.randrange(y_min, games.screen.width - y_min)
            x = self.ship.x + x_distance
            y = self.ship.y + y_distance
            # vozvrat objekta vseredinu vikna
            x %= games.screen.width
            y %= games.screen.height

            new_asteroid = Asteroid(game=self, x=x, y=y, size=Asteroid.LARGE)
            games.screen.add(new_asteroid)

        level_msg = games.Message(
            value=f"level {self.level}",
            size=30,
            color=color.white,
            x=games.screen.width / 2,
            y=games.screen.height / 2,
            lifetime=3 * games.screen.fps,
            is_collideable=False,
        )
        games.screen.add(level_msg)
        if self.level > 1:
            self.sound.play()

    def end(self):
        end_msg = games.Message(
            value="Game Over. Press `q` key for exit.",
            size=40,
            color=color.white,
            x=games.screen.width / 2,
            y=games.screen.height / 2,
            lifetime=5 * games.screen.fps,
            after_death=games.screen.quit,
            is_collideable=False,
        )
        games.screen.add(end_msg)

        if games.keyboard.is_pressed(games.K_q):
            games.screen.quit()


def main():
    game = Game()
    game.play()


if __name__ == "__main__":
    main()
