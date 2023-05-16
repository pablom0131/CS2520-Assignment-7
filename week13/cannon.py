import numpy as np
import pygame as pg
from random import randint, gauss
import random

pg.init()
pg.font.init()

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
DARKGREEN = (1, 50, 32)
BLUEVIOLET = (138, 43, 226)
YELLOW = (255,255,0)
GREEN = (0,255,0)
SCREEN_SIZE = (800, 600)


def rand_color():
    return (randint(0, 255), randint(0, 255), randint(0, 255))


class GameObject:
    def move(self):
        pass

    def draw(self, screen):
        pass


class Shell(GameObject):
    """The projectile class. Creates a projectile, controls its movement and implements its rendering."""
    def __init__(self, coord, vel, rad=20, color=None, p_type=0):
        """Constructor method. Initializes projectile's parameters and initial values."""
        self.coord = coord
        self.p_type = p_type
        self.vel = vel
        if self.p_type == 0:
            self.rad = rad
        elif self.p_type == 1:
            self.vel[0] *= 1.5
            self.vel[1] *= 1.5
            self.rad = 10
        else:
            self.vel[0] *= 0.75
            self.vel[1] *= 0.75
            self.rad = 30
        if color is None:
            color = rand_color()
        self.color = color
        self.rad = rad
        self.is_alive = True

    def check_corners(self, refl_ort=0.8, refl_par=0.9):
        """Reflects projectile's velocity when ball bumps into the screen corners. Implements inelastic rebounce."""
        for i in range(2):
            if self.coord[i] < self.rad:
                self.coord[i] = self.rad
                self.vel[i] = -int(self.vel[i] * refl_ort)
                self.vel[1-i] = int(self.vel[1-i] * refl_par)
            elif self.coord[i] > SCREEN_SIZE[i] - self.rad:
                self.coord[i] = SCREEN_SIZE[i] - self.rad
                self.vel[i] = -int(self.vel[i] * refl_ort)
                self.vel[1-i] = int(self.vel[1-i] * refl_par)

    def move(self, time=1, grav=0):
        """Moves the projectile according to its velocity and time step.

        Changes the projectile's velocity due to gravitational force.
        """
        self.vel[1] += grav
        for i in range(2):
            self.coord[i] += time * self.vel[i]
        self.check_corners()
        if self.vel[0]**2 + self.vel[1]**2 < 2**2 and self.coord[1] > SCREEN_SIZE[1] - 2*self.rad:
            self.is_alive = False

    def draw(self, screen):
        """Draws the projectile on appropriate surface."""
        pg.draw.circle(screen, self.color, self.coord, self.rad)


class Tank(GameObject):
    """Tank class. Manages its rendering, movement and striking."""
    def __init__(self, coord=[30, SCREEN_SIZE[1]-25], angle=0, max_pow=80, min_pow=10, color=DARKGREEN, p_type=0):
        """Constructor method. Sets coordinate, direction, minimum and maximum power, and color of the gun."""
        self.coord = coord
        self.angle = angle
        self.max_pow = max_pow
        self.min_pow = min_pow
        self.color = color
        self.active = False
        self.pow = min_pow
        self.p_type = p_type

    def activate(self):
        """Activates gun's charge."""
        self.active = True

    def gain(self, inc=2):
        """Increases current gun charge power."""
        if self.active and self.pow < self.max_pow:
            self.pow += inc

    def strike(self):
        """Creates projectile, according to gun's direction and current charge power."""
        vel = self.pow
        angle = self.angle
        if self.p_type == 0:
            ball = Shell(list(self.coord), [
                        int(vel * np.cos(angle)), int(vel * np.sin(angle))], p_type=0)
        elif self.p_type == 1:
            ball = Shell(list(self.coord), [
                        int(vel * np.cos(angle)), int(vel * np.sin(angle))], p_type=1)
        else:
            ball = Shell(list(self.coord), [
                        int(vel * np.cos(angle)), int(vel * np.sin(angle))], p_type=2)
        self.pow = self.min_pow
        self.active = False
        return ball

    def set_angle(self, target_pos):
        """Sets gun's direction to target position."""
        self.angle = np.arctan2(
            target_pos[1] - self.coord[1], target_pos[0] - self.coord[0])

    def move(self, inc):
        """Changes horizontal position of the gun."""
        x = self.coord[0] + inc
        if x > SCREEN_SIZE[0] - 30:
            self.coord[0] = SCREEN_SIZE[0] - 30
        elif x < 30:
            self.coord[0] = 30
        else:
            self.coord[0] = x

    def draw(self, screen):
        """Draws the Tank on the screen."""
        # Tank body
        static_rect = pg.Rect(self.coord[0] - 60//2, self.coord[1], 60, 20)
        pg.draw.rect(screen, self.color, static_rect)

        pg.draw.circle(screen, self.color,
                       (self.coord[0] - 20, self.coord[1] + 18), 7)
        pg.draw.circle(screen, self.color,
                       (self.coord[0], self.coord[1] + 18), 7)
        pg.draw.circle(screen, self.color,
                       (self.coord[0] + 20, self.coord[1] + 18), 7)

        # Cannon
        gun_shape = []
        vec_1 = np.array([int(5*np.cos(self.angle - np.pi/2)),
                         int(5*np.sin(self.angle - np.pi/2))])
        vec_2 = np.array([int(self.pow*np.cos(self.angle)),
                         int(self.pow*np.sin(self.angle))])
        gun_pos = np.array(self.coord)
        gun_shape.append((gun_pos + vec_1).tolist())
        gun_shape.append((gun_pos + vec_1 + vec_2).tolist())
        gun_shape.append((gun_pos + vec_2 - vec_1).tolist())
        gun_shape.append((gun_pos - vec_1).tolist())
        pg.draw.polygon(screen, self.color, gun_shape)


class BotTank(Tank):
    """Bot tank class. Creates bot tank and handles its movement and striking"""
    def __init__(self, coord=[400, SCREEN_SIZE[1] - 25], angle=0, max_pow=80, min_pow=10):
        """Constructor method. Calls superclass constructor and sets values"""
        super().__init__(coord, angle, max_pow, min_pow, color=RED)
        self.direction = 1
        self.move_counter = 0
        self.move_threshold = 50

    def move_left(self):
        """Moves gun left."""
        self.move(-15)

    def move_right(self):
        """Moves gun right"""
        self.move(15)

    def update(self):
        """Updates bot tank movement, gun position, and fire rate."""
        self.move_counter += 1
        if self.move_counter >= self.move_threshold:
            self.move_counter = 0
            self.direction *= -1
            if self.direction == -1:
                self.move_left()
            else:
                self.move_right()
        if random.randint(0,100) < 5:
            target_angle = random.uniform(-np.pi/4, np.pi/4)
            self.set_angle([self.coord[0] + 100 * np.cos(target_angle), self.coord[1] + 100 * np.sin(target_angle)])
            self.activate()
            return self.strike()


class Target(GameObject):
    """Target class. Creates target, manages its rendering and collision with a ball event."""
    def __init__(self, coord=None, color=None, rad=30):
        """Constructor method. Sets coordinate, color and radius of the target."""
        if coord is None:
            coord = [randint(rad, SCREEN_SIZE[0] - rad),
                     randint(rad, SCREEN_SIZE[1] - rad)]
        self.coord = coord
        self.rad = rad

        if color is None:
            color = YELLOW
        self.color = color

    def check_collision(self, ball):
        """Checks whether the ball bumps into target."""
        dist = sum([(self.coord[i] - ball.coord[i])**2 for i in range(2)])**0.5
        min_dist = self.rad + ball.rad
        return dist <= min_dist

    def draw(self, screen):
        """Draws the target on the screen"""
        pg.draw.circle(screen, self.color, self.coord, self.rad)

    def move(self):
        """This type of target can't move at all."""
        pass


class MovingTargets(Target):
    """Moving target class. Creates moving target, manages its rendering and collision with a ball event."""
    def __init__(self, coord=None, color=GREEN, rad=30):
        """Constructor method. Sets coordinate, color, and radius of target"""
        super().__init__(coord, color, rad)
        self.vx = randint(-2, +2)
        self.vy = randint(-2, +2)
        self.falling_bombs = []

    def move(self):
        """Changes position of target."""
        self.coord[0] += self.vx
        self.coord[1] += self.vy

        if randint(1, 100) < 5:
            self.falling_bombs.append(TargetBombs(list(self.coord)))

        for bombs in self.falling_bombs:
            bombs.move()
            if not bombs.is_alive:
                self.falling_bombs.remove(bombs)

    def draw(self, screen):
        """Draws the target on the screen."""
        super().draw(screen)
        for bombs in self.falling_bombs:
            bombs.draw(screen)


class VerticalTargets(Target):
    """Creates a target that moves vertically. Handles its movement."""
    def __init__(self, coord=None, color=WHITE, rad=30):
        """Constructor method. Calls superclass constructor and sets values."""
        super().__init__(coord, color, rad)
        self.vy = randint(-2, +2)

    def move(self):
        """Changes position of target."""
        self.coord[1] += self.vy


class HorizontalTargets(Target):
    """Creates a target that moves horizontally. Handles its movement."""
    def __init__(self, coord=None, color=RED, rad=30):
        """Constructor method. Calls superclass constructor and sets values."""
        super().__init__(coord, color, rad)
        self.vx = randint(-2, +2)

    def move(self):
        """Changes position of target."""
        self.coord[0] += self.vx


class TargetBombs:
    """Creates bombs from targets. Handles its movement and rendering."""
    def __init__(self, coord, vel=(0, 2), width=10, height=5, color=(255, 0, 0)):
        """Constructor method. Sets values."""
        self.coord = coord
        self.vel = vel
        self.width = width
        self.height = height
        self.color = color
        self.is_alive = True

    def move(self):
        """Changes bomb position."""
        self.coord[1] += self.vel[1]
        if self.coord[1] > SCREEN_SIZE[1]:
            self.is_alive = False

    def draw(self, screen):
        """Draws the bombs on the screen"""
        pg.draw.rect(screen, self.color,
                     (self.coord[0], self.coord[1], self.width, self.height))


class ScoreTable:
    """Score table class. Keeps track of the score and creates a scoreboard."""
    def __init__(self, t_destr=0, b_used=0, p_chosen="reg"):
        """Constructor method. Sets values."""
        self.t_destr = t_destr
        self.b_used = b_used
        self.p_chosen = p_chosen
        self.font = pg.font.SysFont("dejavusansmono", 25)

    def score(self):
        """Score calculation method."""
        return self.t_destr - self.b_used

    def draw(self, screen):
        """Draws the scoreboard on the screen."""
        score_surf = []
        score_surf.append(self.font.render(
            "Destroyed: {}".format(self.t_destr), True, WHITE))
        score_surf.append(self.font.render(
            "Balls used: {}".format(self.b_used), True, WHITE))
        score_surf.append(self.font.render(
            "Total: {}".format(self.score()), True, RED))
        score_surf.append(self.font.render(
            "Projectile Chosen: {}".format(self.p_chosen), True, WHITE))
        for i in range(4):
            screen.blit(score_surf[i], [10, 10 + 30*i])


class Manager:
    """Class that manages event handling, projectile motion and collision, target creation, etc."""
    def __init__(self, n_targets=1):
        """Constructor method. Sets values."""
        self.balls = []
        self.gun = Tank()
        self.targets = []
        self.score_t = ScoreTable()
        self.n_targets = n_targets
        self.bot_tank = BotTank()
        self.new_mission()

    def new_mission(self):
        """Adds new targets."""
        for i in range(self.n_targets):
            self.targets.append(MovingTargets(rad=randint(max(1, 30 - 2*max(0, self.score_t.score())),
                                                          30 - max(0, self.score_t.score()))))
            self.targets.append(Target(rad=randint(max(1, 30 - 2*max(0, self.score_t.score())),
                                                   30 - max(0, self.score_t.score()))))
            self.targets.append(VerticalTargets(rad=randint(max(1, 30 - 2*max(0, self.score_t.score())),
                                                            30 - max(0, self.score_t.score()))))
            self.targets.append(HorizontalTargets(rad=randint(max(1, 30 - 2*max(0, self.score_t.score())),
                                                            30 - max(0, self.score_t.score()))))

    def process(self, events, screen):
        """Runs all necessary method for each iteration. Adds new targets, if previous are destroyed."""
        done = self.handle_events(events)

        if pg.mouse.get_focused():
            mouse_pos = pg.mouse.get_pos()
            self.gun.set_angle(mouse_pos)

        self.move()
        self.collide()
        self.draw(screen)

        if len(self.targets) == 0 and len(self.balls) == 0:
            self.new_mission()

        return done

    def handle_events(self, events):
        """Handles events from keyboard, mouse, etc."""
        done = False
        for event in events:
            if event.type == pg.QUIT:
                done = True
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_LEFT:
                    self.gun.move(-40)
                elif event.key == pg.K_RIGHT:
                    self.gun.move(40)
                elif event.key == pg.K_e:
                    if self.score_t.p_chosen == "reg":
                        self.score_t.p_chosen = "fast"
                        self.gun.p_type = 1
                    elif self.score_t.p_chosen == "fast":
                        self.score_t.p_chosen = "slow"
                        self.gun.p_type = 2
                    else:
                        self.score_t.p_chosen = "reg"
                        self.gun.p_type = 0

            elif event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.gun.activate()
            elif event.type == pg.MOUSEBUTTONUP:
                if event.button == 1:
                    self.balls.append(self.gun.strike())
                    self.score_t.b_used += 1
        return done

    def draw(self, screen):
        """Runs projectiles', tanks', targets' and score table's drawing methods."""
        for ball in self.balls:
            ball.draw(screen)
        for target in self.targets:
            target.draw(screen)
        self.gun.draw(screen)
        self.score_t.draw(screen)
        self.bot_tank.draw(screen)

    def move(self):
        """Runs projectiles' and tanks' movement methods, removes dead balls."""
        dead_balls = []
        for i, ball in enumerate(self.balls):
            ball.move(grav=2)
            if not ball.is_alive:
                dead_balls.append(i)
        for i in reversed(dead_balls):
            self.balls.pop(i)
        for i, target in enumerate(self.targets):
            target.move()
        self.gun.gain()
        self.bot_tank.update()

    def collide(self):
        """Checks whether projectiles bump into targets, sets projectiles' alive trigger."""
        collisions = []
        targets_c = []
        for i, ball in enumerate(self.balls):
            for j, target in enumerate(self.targets):
                if target.check_collision(ball):
                    collisions.append([i, j])
                    targets_c.append(j)
        targets_c.sort()
        for j in reversed(targets_c):
            self.score_t.t_destr += 1
            self.targets.pop(j)


# Driver code
screen = pg.display.set_mode(SCREEN_SIZE)
pg.display.set_caption("The gun of Khiryanov")

done = False
clock = pg.time.Clock()

mgr = Manager(n_targets=2)

while not done:
    clock.tick(15)
    screen.fill(BLACK)

    done = mgr.process(pg.event.get(), screen)

    pg.display.flip()

pg.quit()