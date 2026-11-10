import tkinter as tk
import math
import random

class GameObject(object):
    def __init__(self, canvas, item):
        self.canvas = canvas
        self.item = item

    def get_position(self):
        return self.canvas.coords(self.item)

    def move(self, x, y):
        self.canvas.move(self.item, x, y)

    def delete(self):
        self.canvas.delete(self.item)

class Ball(GameObject):
    def __init__(self, canvas, x, y):
        self.radius = 8 # Diperkecil sedikit agar lebih elegan
        # Arah awal diacak sedikit agar tidak monoton
        self.direction = [random.choice([0.5, -0.5, 1, -1]), -1]
        self._normalize_direction()
        self.speed = 7.0
        item = canvas.create_oval(x-self.radius, y-self.radius,
                                  x+self.radius, y+self.radius,
                                  fill='#ecf0f1', outline='#bdc3c7')
        super(Ball, self).__init__(canvas, item)

    def _normalize_direction(self):
        # Memastikan kecepatan bola konstan di segala arah menggunakan vektor
        length = math.hypot(self.direction[0], self.direction[1])
        if length == 0:
            self.direction = [0, -1]
            length = 1
        self.direction[0] /= length
        self.direction[1] /= length

    def update(self):
        coords = self.get_position()
        width = self.canvas.winfo_width()
        
        # Pantulan dinding kiri/kanan
        if coords[0] <= 0 or coords[2] >= width:
            self.direction[0] *= -1
            # Mencegah bola menempel di dinding
            if coords[0] <= 0:
                self.canvas.move(self.item, 1, 0)
            else:
                self.canvas.move(self.item, -1, 0)
                
        # Pantulan atap
        if coords[1] <= 0:
            self.direction[1] *= -1
            
        x = self.direction[0] * self.speed
        y = self.direction[1] * self.speed
        self.move(x, y)

    def collide(self, game_objects, paddle):
        coords = self.get_position()
        x = (coords[0] + coords[2]) * 0.5
        y = (coords[1] + coords[3]) * 0.5
        
        hit_brick = False

        for game_object in game_objects:
            if isinstance(game_object, Paddle):
                # FISIKA PANTULAN DINAMIS: Sudut tergantung letak benturan di paddle
                paddle_coords = game_object.get_position()
                paddle_center = (paddle_coords[0] + paddle_coords[2]) / 2
                
                # Offset bernilai antara -1 (kiri) sampai 1 (kanan)
                offset = (x - paddle_center) / (game_object.width / 2)
                
                self.direction[0] = offset * 1.5 # Sensitivitas pantulan
                self.direction[1] = -1 # Selalu pantul ke atas
                self._normalize_direction()
                
            elif isinstance(game_object, Brick):
                # PERBAIKAN: Ambil koordinat SEBELUM bata dihancurkan
                b_coords = game_object.get_position() 
                
                game_object.hit()
                hit_brick = True
                
                # PERBAIKAN: Cek apakah koordinat valid sebelum memantulkan bola
                if len(b_coords) == 4:
                    if x < b_coords[0] or x > b_coords[2]:
                        self.direction[0] *= -1
                    else:
                        self.direction[1] *= -1

        return hit_brick

class Paddle(GameObject):
    def __init__(self, canvas, x, y):
        self.width = 110
        self.height = 12
        self.ball = None
        item = canvas.create_rectangle(x - self.width / 2,
                                       y - self.height / 2,
                                       x + self.width / 2,
                                       y + self.height / 2,
                                       fill='#f39c12', outline='#d35400', width=2)
        super(Paddle, self).__init__(canvas, item)

    def set_ball(self, ball):
        self.ball = ball

    def move(self, offset):
        coords = self.get_position()
        width = self.canvas.winfo_width()
        if coords[0] + offset >= 0 and coords[2] + offset <= width:
            super(Paddle, self).move(offset, 0)
            if self.ball is not None:
                self.ball.move(offset, 0)

class Brick(GameObject):
    # Skema warna gradasi modern (Neon/Pastel)
    COLORS = {1: '#2ecc71', 2: '#1abc9c', 3: '#3498db', 4: '#9b59b6', 5: '#e74c3c'}

    def __init__(self, canvas, x, y, hits):
        self.width = 70
        self.height = 22
        self.hits = hits
        color = Brick.COLORS.get(hits, '#e74c3c')
        item = canvas.create_rectangle(x - self.width / 2,
                                       y - self.height / 2,
                                       x + self.width / 2,
                                       y + self.height / 2,
                                       fill=color, outline='#2c3e50', width=2, tags='brick')
        super(Brick, self).__init__(canvas, item)

    def hit(self):
        self.hits -= 1
        if self.hits == 0:
            self.delete()
        else:
            color = Brick.COLORS.get(self.hits, '#e74c3c')
            self.canvas.itemconfig(self.item, fill=color)

class Game(tk.Frame):
    def __init__(self, master):
        super(Game, self).__init__(master)
        self.lives = 3
        self.score = 0
        self.combo = 1
        self.level = 1
        self.width = 610
        self.height = 450
        
        # UI Setup
        self.canvas = tk.Canvas(self, bg='#1a252c', # Warna background lebih elegan
                                width=self.width,
                                height=self.height)
        self.canvas.pack()
        self.pack()

        self.items = {}
        self.ball = None
        self.paddle = Paddle(self.canvas, self.width/2, 400)
        self.items[self.paddle.item] = self.paddle
        
        self.hud = None
        self.score_hud = None
        self.combo_hud = None
        self.level_hud = None
        
        self.generate_level()
        self.setup_game()
        self.canvas.focus_set()
        
        # Smooth movement variables
        self.left_pressed = False
        self.right_pressed = False
        
        self.canvas.bind('<KeyPress-Left>', self.press_left)
        self.canvas.bind('<KeyRelease-Left>', self.release_left)
        self.canvas.bind('<KeyPress-Right>', self.press_right)
        self.canvas.bind('<KeyRelease-Right>', self.release_right)
        
        self.update_paddle_movement()

    def generate_level(self):
        # Membersihkan bata lama jika ada
        for item in self.canvas.find_withtag('brick'):
            self.canvas.delete(item)
            
        self.items = {self.paddle.item: self.paddle}
        
        # Semakin tinggi level, semakin banyak nyawa bata
        rows = min(6, 3 + self.level)
        for row in range(rows):
            for x in range(5, self.width - 5, 75):
                hits = min(5, rows - row + (self.level // 2))
                self.add_brick(x + 37.5, 60 + (row * 25), hits)

    def press_left(self, event): self.left_pressed = True
    def release_left(self, event): self.left_pressed = False
    def press_right(self, event): self.right_pressed = True
    def release_right(self, event): self.right_pressed = False

    def update_paddle_movement(self):
        if self.left_pressed:
            self.paddle.move(-12)
        if self.right_pressed:
            self.paddle.move(12)
        self.after(20, self.update_paddle_movement)

    def setup_game(self):
        self.add_ball()
        self.update_hud()
        self.text = self.draw_text(self.width/2, self.height/2 + 30, 'Press SPACE to Start\nUse LEFT/RIGHT Arrows', size=20)
        self.canvas.bind('<space>', lambda _: self.start_game())

    def add_ball(self):
        if self.ball is not None:
            self.ball.delete()
        paddle_coords = self.paddle.get_position()
        x = (paddle_coords[0] + paddle_coords[2]) * 0.5
        self.ball = Ball(self.canvas, x, paddle_coords[1] - 15)
        # Menyesuaikan kecepatan bola dengan level
        self.ball.speed = 6.0 + (self.level * 0.5) 
        self.paddle.set_ball(self.ball)

    def add_brick(self, x, y, hits):
        brick = Brick(self.canvas, x, y, hits)
        self.items[brick.item] = brick

    def draw_text(self, x, y, text, size='40'):
        font = ('Consolas', size, 'bold')
        return self.canvas.create_text(x, y, text=text, font=font, fill='#ecf0f1', justify=tk.CENTER)

    def update_hud(self):
        # Lives
        lives_txt = f'❤ {self.lives}'
        if self.hud is None:
            self.hud = self.draw_text(40, 20, lives_txt, 14)
            self.canvas.itemconfig(self.hud, fill='#e74c3c')
        else:
            self.canvas.itemconfig(self.hud, text=lives_txt)
            
        # Score
        score_txt = f'SCORE: {self.score:05d}'
        if self.score_hud is None:
            self.score_hud = self.draw_text(self.width/2, 20, score_txt, 14)
        else:
            self.canvas.itemconfig(self.score_hud, text=score_txt)

        # Level
        level_txt = f'LEVEL: {self.level}'
        if self.level_hud is None:
            self.level_hud = self.draw_text(self.width - 60, 20, level_txt, 14)
        else:
            self.canvas.itemconfig(self.level_hud, text=level_txt)

        # Combo
        combo_txt = f'{self.combo}x COMBO!' if self.combo > 1 else ''
        if self.combo_hud is None:
            self.combo_hud = self.draw_text(self.width/2, 45, combo_txt, 12)
            self.canvas.itemconfig(self.combo_hud, fill='#f1c40f')
        else:
            self.canvas.itemconfig(self.combo_hud, text=combo_txt)

    def start_game(self):
        self.canvas.unbind('<space>')
        self.canvas.delete(self.text)
        self.paddle.ball = None
        self.game_loop()

    def game_loop(self):
        self.check_collisions()
        num_bricks = len(self.canvas.find_withtag('brick'))
        
        if num_bricks == 0: 
            # LOGIKA NAIK LEVEL
            self.ball.speed = None
            self.level += 1
            self.combo = 1
            self.text = self.draw_text(self.width/2, self.height/2, f'LEVEL {self.level} CLEARED!', 25)
            self.after(2000, self.start_next_level)
            
        elif self.ball.get_position()[3] >= self.height: 
            self.ball.speed = None
            self.lives -= 1
            self.combo = 1
            if self.lives < 0:
                self.canvas.delete(self.combo_hud)
                self.draw_text(self.width/2, self.height/2 - 20, 'GAME OVER', 35)
                self.draw_text(self.width/2, self.height/2 + 30, f'Final Score: {self.score}', 18)
            else:
                self.after(1000, self.setup_game)
        else:
            self.ball.update()
            self.after(16, self.game_loop) # ~60 FPS

    def start_next_level(self):
        self.canvas.delete(self.text)
        self.generate_level()
        self.setup_game()

    def check_collisions(self):
        ball_coords = self.ball.get_position()
        items = self.canvas.find_overlapping(*ball_coords)
        objects = [self.items[x] for x in items if x in self.items]
        
        # Mengecek apakah bola mengenai paddle atau bata
        hit_brick = self.ball.collide(objects, self.paddle)
        
        # Logika Combo & Score
        if any(isinstance(obj, Paddle) for obj in objects):
            self.combo = 1 # Reset combo jika menyentuh paddle
            
        if hit_brick:
            self.score += (10 * self.combo)
            self.combo += 1
            
        if hit_brick or any(isinstance(obj, Paddle) for obj in objects):
            self.update_hud()

if __name__ == '__main__':
    root = tk.Tk()
    root.title('Pro Brick Breaker')
    root.resizable(False, False) # Mencegah window di-resize agar UI tidak rusak
    game = Game(root)
    game.mainloop()