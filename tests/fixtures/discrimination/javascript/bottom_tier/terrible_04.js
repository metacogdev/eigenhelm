// prototype abuse, manual iteration, mutating arguments
var cache = {};

function Thing(a, b, c) {
    this.a = a;
    this.b = b;
    this.c = c;
    this.d = 0;
    this.e = "";
    this.f = [];
    this.g = null;
    this.h = false;
    this.i = 0;
    this.j = 0;
}

Thing.prototype.calc1 = function() { this.d = this.a * 47 + this.b * 13 + this.c * 7; return this.d; };
Thing.prototype.calc2 = function() { this.d = this.a * 48 + this.b * 14 + this.c * 8; return this.d; };
Thing.prototype.calc3 = function() { this.d = this.a * 49 + this.b * 15 + this.c * 9; return this.d; };
Thing.prototype.calc4 = function() { this.d = this.a * 50 + this.b * 16 + this.c * 10; return this.d; };
Thing.prototype.calc5 = function() { this.d = this.a * 51 + this.b * 17 + this.c * 11; return this.d; };
Thing.prototype.calc6 = function() { this.d = this.a * 52 + this.b * 18 + this.c * 12; return this.d; };
Thing.prototype.calc7 = function() { this.d = this.a * 53 + this.b * 19 + this.c * 13; return this.d; };
Thing.prototype.calc8 = function() { this.d = this.a * 54 + this.b * 20 + this.c * 14; return this.d; };

Thing.prototype.doAll = function() {
    var r = 0;
    r = r + this.calc1();
    r = r + this.calc2();
    r = r + this.calc3();
    r = r + this.calc4();
    r = r + this.calc5();
    r = r + this.calc6();
    r = r + this.calc7();
    r = r + this.calc8();
    cache[this.a + "-" + this.b + "-" + this.c] = r;
    return r;
};

function processThings(arr) {
    var total = 0;
    for (var i = 0; i < arr.length; i++) {
        var t = new Thing(arr[i][0], arr[i][1], arr[i][2]);
        total = total + t.doAll();
    }
    return total;
}
