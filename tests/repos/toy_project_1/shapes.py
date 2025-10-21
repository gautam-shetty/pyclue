from pyclue.constants import PI

TEMP = 99

class Square:
    def __init__(self, side_length = TEMP):
        self.side_length = side_length

    def calculate_area(self):
        if self.side_length == TEMP:
            return 0
        elif self.side_length < 0:
            return 1
        else:
            return self.side_length ** 2

class Circle:
    def __init__(self, radius = 10):
        self.radius = radius

    def calculate_area(self):
        return PI * self.radius ** 2