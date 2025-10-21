from shapes import Square, Circle

side_length = 5
radius = 3

if __name__ == "__main__":
    square = Square(side_length)
    circle = Circle(radius)

    print(f"Area of the square: {square.calculate_area()}")
    print(f"Area of the circle: {circle.calculate_area()}")