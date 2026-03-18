import math


def circle_area(radius):
    return math.pi * radius * radius


def rectangle_area(width, height):
    return width * height


def triangle_area(base, height):
    return 0.5 * base * height


def trapezoid_area(a, b, height):
    return 0.5 * (a + b) * height


def square_perimeter(side):
    return 4 * side


def circle_circumference(radius):
    return 2 * math.pi * radius


def print_areas():
    print("Circle r=5:", circle_area(5))
    print("Rectangle 4x6:", rectangle_area(4, 6))
    print("Triangle b=3 h=8:", triangle_area(3, 8))
