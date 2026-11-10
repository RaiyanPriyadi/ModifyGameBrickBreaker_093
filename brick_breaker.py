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

