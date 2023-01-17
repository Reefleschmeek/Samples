import pyglet as pg
from pyglet.window import key
import math
import random
import ast

pg.options['debug_gl'] = False
keys = key.KeyStateHandler()
batch = pg.graphics.Batch()
background = pg.graphics.OrderedGroup(0)
foreground = pg.graphics.OrderedGroup(1)

SIM_DT = 1/30
SIM_STEPS = 60

file = open('assets\\settings.txt')
content = file.read().split('\n')
file.close()
content[0] = content[0][content[0].index('{'):]
player_stats = ast.literal_eval(content[0])
content[1] = content[1][content[1].index('{'):]
enemy_stats = ast.literal_eval(content[1])

#Returns the angle a projectile with speed v originating from (x0, y0) must be shot at to hit an object that has velocity (vx, vy) at (x, y).
def calc_angle(x, y, vx, vy, x0, y0, v):
    
    dx = x-x0
    dy = y-y0
    
    descriminant = dx**2*v**2-(dy*v+dy*vx-dx*vy)*(-dy*v+dy*vx-dx*vy)
    if descriminant < 0:
        return None
    denominator = dy*v + dy*vx - dx*vy
    if denominator == 0:
        angle_1 = 0
        angle_2 = math.pi
    else:
        quadratic_root_1 = (-dx*v + descriminant**(1/2))/denominator
        quadratic_root_2 = (-dx*v - descriminant**(1/2))/denominator
        angle_1 = 2*math.atan(quadratic_root_1)
        angle_2 = 2*math.atan(quadratic_root_2)
    
    if angle_1 < 0:
        angle_1 += 2*math.pi
    if angle_2 < 0:
        angle_2 += 2*math.pi
    
    time_1_x = 0
    time_1_y = 0
    time_2_x = 0
    time_2_y = 0
    v_relative = v*math.cos(angle_1)-vx
    if v_relative != 0:
        time_1_x = dx/v_relative
    v_relative = v*math.sin(angle_1)-vy
    if v_relative != 0:
        time_1_y = dy/v_relative
    v_relative = v*math.cos(angle_2)-vx
    if v_relative != 0:
        time_2_x = dx/v_relative
    v_relative = v*math.sin(angle_2)-vy
    if v_relative != 0:
        time_2_y = dy/v_relative
    
    if time_1_x == 0:
        time_1 = time_1_y
    else:
        time_1 = time_1_x
    if time_2_x == 0:
        time_2 = time_2_y
    else:
        time_2 = time_2_x
    
    if time_1 > 0:
        return angle_1
    if time_2 > 0:
        return angle_2
    return None

def euclidean_distance(x0, y0, x1, y1):
    return ((x1-x0)**2 + (y1-y0)**2)**(1/2)

def angular_distance(a0, a1):
    dtheta = a1-a0
    if dtheta > math.pi:
        dtheta -= 2*math.pi
    if dtheta < -math.pi:
        dtheta += 2*math.pi
    return dtheta

def get_obj_by_name(name):
    objects = []
    for obj in Game.objects:
        if obj.name == name:
            objects.append(obj)
    return objects

def get_obj_by_class(class_):
    objects = []
    for obj in Game.objects:
        if isinstance(obj, class_):
            objects.append(obj)
    return objects

class Game(pg.window.Window):
    
    sim_frames = []
    objects = []
    width = None
    height = None
    state = None
    timer = 0
    
    def __init__(self):
        Game.width = 1000
        Game.height = 1000
        super().__init__(width=Game.width, height=Game.height)
        self.push_handlers(keys)
        pg.clock.schedule_interval(self.update, 1/60)
        
        Game.state = 'battle'
        self.next_state()
    
    def next_state(self):
        if Game.state == 'main':
            self.clear_objects()
            Game.state = 'ready'
            player = PlayerShip(x=Game.width/2, y=1/4*Game.height)
            player.angle = 1/4*math.pi
            player.update(0)
            Game.objects.append(player)
            enemy = EnemyShip(x=Game.width/2, y=3/4*Game.height)
            enemy.angle = 5/4*math.pi
            enemy.update(0)
            Game.objects.append(enemy)
            text = TextObject(text='3', x=Game.width/2, y=Game.height/2, size=30)
            Game.objects.append(text)
            Game.timer = 3.999
        
        elif Game.state == 'ready':
            Game.state = 'battle'
            get_obj_by_name('text')[0].text = ''
            Game.timer = 3
        
        elif Game.state == 'battle' and len(get_obj_by_class(Ship)) < 2:
            self.clear_objects()
            Game.state = 'main'
            player = EnemyShip(x=Game.width/2, y=1/4*Game.height)
            player.name = 'player'
            player.angle = 1/4*math.pi
            Game.objects.append(player)
            enemy = EnemyShip(x=Game.width/2, y=3/4*Game.height)
            enemy.angle = 5/4*math.pi
            Game.objects.append(enemy)
            text = TextObject(text='DOGFIGHT', x=Game.width/2, y=Game.height/2+30, size=30)
            Game.objects.append(text)
            text = TextObject(text='Press Spacebar To Play', x=Game.width/2, y=Game.height/2-30, size=20)
            Game.objects.append(text)
            Game.timer = 3
    
    def sim_projectiles(self):
        Game.sim_frames.clear()
        for step in range(SIM_STEPS):
            time_frame = []
            for proj in get_obj_by_class(Projectile):
                dt = step*SIM_DT
                coords = (proj.game_x+proj.vx*dt, proj.game_y+proj.vy*dt)
                time_frame.append(coords)
            Game.sim_frames.append(time_frame)
    
    def clear_objects(self):
        for obj in self.objects:
            obj.delete()
        self.objects.clear()
    
    def update(self, dt):
        self.sim_projectiles()
        if Game.state == 'ready':
            Game.timer -= dt
            get_obj_by_name('text')[0].text = str(int(Game.timer))
            if Game.timer <= 1:
                self.next_state()
        else:
            for obj in Game.objects:
                obj.update(dt)
                if not obj.alive:
                    obj.delete()
                    Game.objects.remove(obj)
        if Game.state == 'battle' and (len(get_obj_by_class(PlayerShip)) == 0 or len(get_obj_by_class(EnemyShip)) == 0):
            Game.timer -= dt
            if get_obj_by_name('text')[0].text == '' and len(get_obj_by_class(PlayerShip)) == 0:
                get_obj_by_name('text')[0].text = 'DEFEAT'
            if get_obj_by_name('text')[0].text == '' and len(get_obj_by_class(EnemyShip)) == 0:
                get_obj_by_name('text')[0].text = 'VICTORY'
            if Game.timer <= 0:
                self.next_state()
        if Game.state == 'main' and len(get_obj_by_class(EnemyShip)) < 2:
            Game.timer -= dt
            if Game.timer <= 0:
                for obj in get_obj_by_class(GameObject):
                    obj.alive = False
                player = EnemyShip(x=Game.width/2, y=1/4*Game.height)
                player.name = 'player'
                player.angle = 1/4*math.pi
                Game.objects.append(player)
                enemy = EnemyShip(x=Game.width/2, y=3/4*Game.height)
                enemy.angle = 5/4*math.pi
                Game.objects.append(enemy)
                Game.timer = 3
    
    def on_key_press(self, symbol, modifiers):
        if symbol == key.SPACE:
            self.next_state()
    
    def on_draw(self):
        self.clear()
        batch.draw()
    
    def on_close(self):
        pg.clock.unschedule(self.update)
        self.clear_objects()
        super().on_close()

class TextObject(pg.text.Label):
    
    def __init__(self, name='text', text='', size=40, x=400, y=400):
        super().__init__(text=text, x=x, y=y, font_size=size, anchor_x='center', anchor_y='center', batch=batch, group=foreground)
        self.name = name
        self.alive = True
    
    def update(self, dt):
        pass

class GameObject(pg.sprite.Sprite):
    
    def __init__(self, sprite, name='', x=0, y=0, width=1, vx=0, vy=0):
        super().__init__(sprite, batch=batch, group=background)
        self.alive = True
        self.name = name
        self.game_x = x
        self.game_y = y
        self.game_width = width
        self.game_height = self.game_width*self.image.height/self.image.width
        self.vx = vx
        self.vy = vy
        self.angle = 0
        self.scale = self.game_width/self.image.width
    
    def update(self, dt):
        self.game_x += self.vx*dt
        self.game_y += self.vy*dt
        if self.game_x > Game.width:
            self.game_x = 0
        if self.game_x < 0:
            self.game_x = Game.width
        if self.game_y > Game.height:
            self.game_y = 0
        if self.game_y < 0:
            self.game_y = Game.height
        c = 0.5*(self.game_width**2+self.game_height**2)**(1/2)
        phi = self.angle+math.atan(self.game_height/self.game_width)
        self.x = self.game_x-c*math.cos(phi)
        self.y = self.game_y-c*math.sin(phi)
        self.angle %= 2*math.pi
        self.rotation = -self.angle*180/math.pi

class Projectile(GameObject):
    
    def __init__(self, x=0, y=0, angle=0, v=1, damage=1, screen_wraps=1):
        super().__init__(sprite=Graphics.Projectile, name='projectile', x=x, y=y, width=20, vx=v*math.cos(angle), vy=v*math.sin(angle))
        self.angle = angle
        self.damage = damage
        self.arming_time = 0.15
        self.timer = 0
        self.screen_wraps = screen_wraps
    
    def update(self, dt):
        self.timer += dt
        if self.timer > self.arming_time:
            for ship in get_obj_by_class(Ship):
                if euclidean_distance(self.game_x, self.game_y, ship.game_x, ship.game_y) < ship.hitbox_radius:
                    ship.take_damage(self.damage)
                    for i in range(5):
                        rand = random.uniform(-math.pi/4, math.pi/4)
                        particle = Particle(self.game_x, self.game_y, self.angle+rand)
                        Game.objects.append(particle)
                    self.alive = False
        super().update(dt)
        if self.game_x == 0 or self.game_y == 0 or self.game_x == Game.width or self.game_y == Game.height:
            self.screen_wraps -= 1
        if self.screen_wraps < 0:
            self.alive = False

class Ship(GameObject):
    
    def __init__(self, sprites, name='ship', x=0, y=0, width=50, hp=5, shot_rate=2, shot_speed=200, shot_damage=1, thrust_force=300, max_speed=100, hitbox_radius=25):
        super().__init__(sprite=sprites['default'], name=name, x=x, y=y, width=width)
        self.sprites = sprites
        self.hp_max = hp
        self.hp = hp
        self.shot_rate = shot_rate
        self.shot_speed = shot_speed
        self.shot_damage = shot_damage
        self.shot_timer = 0.1
        self.thrust_force = thrust_force
        self.max_speed = max_speed
        self.hitbox_radius = hitbox_radius
        self.thrusting = False
        self.hp_bar = TextObject(name=name+'_health', size=20)
    
    def update(self, dt):
        self.shot_timer -= dt
        if self.thrusting:
            self.image = self.sprites['thrust']
            self.thrusting = False
        else:
            self.image = self.sprites['default']
        super().update(dt)
        self.hp_bar.x = self.game_x
        self.hp_bar.y = self.game_y+35
        self.hp_bar.text = '-'*self.hp
        red = int(255*(1-self.hp/self.hp_max))
        blue = int(255*self.hp/self.hp_max)
        self.hp_bar.color = (red, 0, blue, 255)
    
    def thrust(self, dt, backwards=False):
        self.thrusting = True
        if backwards:
            self.vx -= 1/2*self.thrust_force*math.cos(self.angle)*dt
            self.vy -= 1/2*self.thrust_force*math.sin(self.angle)*dt
        else:
            self.vx += self.thrust_force*math.cos(self.angle)*dt
            self.vy += self.thrust_force*math.sin(self.angle)*dt
        v = (self.vx**2+self.vy**2)**(1/2)
        if v > self.max_speed:
            self.vx *= self.max_speed/v
            self.vy *= self.max_speed/v
        return min(v, self.max_speed)
    
    def try_shoot(self):
        if self.shot_timer <= 0:
            self.shoot()
            self.shot_timer = 1/self.shot_rate
    
    def shoot(self):
        projectile = Projectile(self.game_x+self.game_width/2*math.cos(self.angle), self.game_y+self.game_width/2*math.sin(self.angle),
                                angle=self.angle, v=self.shot_speed, damage=self.shot_damage)
        Game.objects.append(projectile)
        Audio.play(Audio.Shoot)
    
    def take_damage(self, amount):
        self.hp -= amount
        Audio.play(Audio.Hit)
        if self.hp <= 0:
            self.alive = False
            for i in range(50):
                rand = random.uniform(0, 2*math.pi)
                particle = Particle(self.game_x, self.game_y, rand, lifetime=1)
                Game.objects.append(particle)
    
    def in_danger(self):
        x = self.game_x
        y = self.game_y
        vx = self.vx
        vy = self.vy
        for step in range(SIM_STEPS):
            for coords in Game.sim_frames[step]:
                proj_x, proj_y = coords
                if euclidean_distance(x%Game.width, y%Game.height, proj_x%Game.width, proj_y%Game.height) < self.hitbox_radius+5:
                    return True
            x += vx*SIM_DT
            y += vy*SIM_DT
        return False
    
    def delete(self):
        self.hp_bar.delete()
        super().delete()

class PlayerShip(Ship):
    
    def __init__(self, x=0, y=0):
        super().__init__(sprites=Graphics.PlayerShip, name='player', x=x, y=y, width=55, **player_stats)
    
    def update(self, dt):
        if keys[key.A]:
            v_angular = 4
            if keys[key.LSHIFT]:
                v_angular = 2
            self.angle += v_angular*dt
        if keys[key.D]:
            v_angular = 4
            if keys[key.LSHIFT]:
                v_angular = 2
            self.angle -= v_angular*dt
        if keys[key.W]:
            self.thrust(dt)
        if keys[key.S]:
            self.thrust(dt, backwards=True)
        if keys[key.SPACE]:
            self.try_shoot()
        super().update(dt)

class EnemyShip(Ship):
    
    def __init__(self, sprites=None, x=0, y=0):
        if sprites == None:
            sprites = Graphics.EnemyShip
        super().__init__(sprites=sprites, name='enemy', x=x, y=y, width=50, **enemy_stats)
        self.state = 'move'
        self.intended_angle = random.uniform(0, 2*math.pi)
    
    def update(self, dt):
        
        if self.state != 'dodge' and self.in_danger():
            escape_angle = self.calc_escape()
            if escape_angle:
                self.state = 'dodge'
                self.intended_angle = escape_angle
        
        if self.state == 'shoot':
            try:
                if self.name == 'enemy':
                    target = get_obj_by_name('player')[0]
                else:
                    target = get_obj_by_name('enemy')[0]
                targeting_angle = calc_angle(target.game_x, target.game_y, target.vx, target.vy, self.game_x, self.game_y, self.shot_speed)
                if targeting_angle:
                    self.intended_angle = targeting_angle
            except:
                self.state = 'move'
                self.intended_angle = random.uniform(0, 2*math.pi)
        
        dtheta = self.intended_angle-self.angle
        if dtheta > math.pi:
            dtheta -= 2*math.pi
        if dtheta < -math.pi:
            dtheta += 2*math.pi
        if abs(dtheta) < 4*dt:
            self.angle = self.intended_angle
        elif dtheta > 0:
            self.angle += 4*dt
        elif dtheta < 0:
            self.angle -= 4*dt
        
        if self.state == 'shoot':
            if self.angle == self.intended_angle:
                self.try_shoot()
        
        if self.state == 'move' or self.state == 'dodge':
            if self.angle == self.intended_angle:
                v = self.thrust(dt)
                if v == self.max_speed:
                    try:
                        if self.name == 'enemy':
                            target = get_obj_by_name('player')[0]
                        else:
                            target = get_obj_by_name('enemy')[0]
                        d = euclidean_distance(self.game_x, self.game_y, target.game_x, target.game_y)
                    except:
                        d = -1000
                    if random.random() < 1.5+30/d:
                        self.state = 'shoot'
                    else:
                        self.state = 'move'
                        self.intended_angle = random.uniform(0, 2*math.pi)
        super().update(dt)
    
    def calc_escape(self):
        escape_angles = []
        for escape_angle in [i/6*math.pi for i in range(12)]:
            safe = True
            x = self.game_x
            y = self.game_y
            vx = self.vx
            vy = self.vy
            accel_start = int(abs(angular_distance(self.angle, escape_angle)/4/SIM_DT))
            for step in range(SIM_STEPS):
                for coords in Game.sim_frames[step]:
                    proj_x, proj_y = coords
                    if euclidean_distance(x%Game.width, y%Game.height, proj_x%Game.width, proj_y%Game.height) < self.hitbox_radius+10:
                        safe = False
                if step >= accel_start:
                    vx += self.thrust_force*math.cos(escape_angle)*SIM_DT
                    vy += self.thrust_force*math.sin(escape_angle)*SIM_DT
                    v = (vx**2+vy**2)**(1/2)
                    if v > self.max_speed:
                        vx *= self.max_speed/v
                        vy *= self.max_speed/v
                x += vx*SIM_DT
                y += vy*SIM_DT
            if safe:
                escape_angles.append(escape_angle)
        if escape_angles:
            return random.choice(escape_angles)
        return None
    
    def shoot(self):
        if self.name == 'enemy':
            target = get_obj_by_name('player')[0]
        else:
            target = get_obj_by_name('enemy')[0]
        d = euclidean_distance(self.game_x, self.game_y, target.game_x, target.game_y)
        if random.random() < 0.0-30/d:
            self.state = 'move'
            self.intended_angle = random.uniform(0, 2*math.pi)
        super().shoot()

class Particle(GameObject):
    
    def __init__(self, x=0, y=0, angle=0, lifetime=0.5):
        v = random.uniform(100, 200)
        super().__init__(sprite=Graphics.Spark, name='particle', x=x, y=y, width=10, vx=v*math.cos(angle), vy=v*math.sin(angle))
        self.angle = angle
        self.lifetime = lifetime
    
    def update(self, dt):
        self.opacity -= 255/self.lifetime*dt
        if self.opacity <= 0:
            self.alive = False
        super().update(dt)

class Graphics:
    
    PlayerShip = {'default':pg.image.load('assets\\ship1.png'),
                  'thrust':pg.image.load('assets\\ship1_thrust.png'),
                  }
    EnemyShip = {'default':pg.image.load('assets\\ship2.png'),
                  'thrust':pg.image.load('assets\\ship2_thrust.png'),
                  }
    Projectile = pg.image.load('assets\\projectile.png')
    Spark = pg.image.load('assets\\spark.png')

class Audio:
    
    def play(sound):
        sound.play()
    
    Shoot = pg.media.load('assets\\shoot.wav', streaming=False)
    Hit = pg.media.load('assets\\hit.wav', streaming=False)

Game()
pg.app.run()