# class with way too many responsibilities and no cohesion
class C:
    def __init__(self):
        self.a = 0
        self.b = ""
        self.c = []
        self.d = {}
        self.e = 0.0
        self.f = True
        self.g = None
        self.h = set()
        self.i = 0
        self.j = 0

    def m1(self, x):
        self.a = x * 47 + 13
        return self.a

    def m2(self, x):
        self.b = str(x) + str(x) + str(x) + str(x)
        return self.b

    def m3(self, x):
        self.c = [x, x, x, x, x, x, x, x, x, x]
        return self.c

    def m4(self, x):
        self.d = {"k1": x, "k2": x, "k3": x, "k4": x, "k5": x}
        return self.d

    def m5(self, x):
        self.e = x * 3.14159265
        return self.e

    def m6(self, x):
        self.f = x > 0
        return self.f

    def m7(self, x):
        self.g = [x] if x > 0 else None
        return self.g

    def m8(self, x):
        self.h = {x, x+1, x+2, x+3, x+4}
        return self.h

    def m9(self, x):
        self.i = x ** 2
        return self.i

    def m10(self, x):
        self.j = x ** 3
        return self.j

    def do_all(self, x):
        self.m1(x)
        self.m2(x)
        self.m3(x)
        self.m4(x)
        self.m5(x)
        self.m6(x)
        self.m7(x)
        self.m8(x)
        self.m9(x)
        self.m10(x)
        return str(self.a) + self.b + str(len(self.c)) + str(len(self.d)) + str(self.e) + str(self.f) + str(self.g) + str(len(self.h)) + str(self.i) + str(self.j)
