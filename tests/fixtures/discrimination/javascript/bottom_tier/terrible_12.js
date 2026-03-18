// god object with everything in one place
var db = { users: [], products: [], orders: [] };

function addUser(n, a, e) { db.users.push({name: n, age: a, email: e, id: db.users.length + 1}); }
function addProduct(n, p, q) { db.products.push({name: n, price: p, qty: q, id: db.products.length + 1}); }
function addOrder(uid, pid, qty) { db.orders.push({userId: uid, productId: pid, qty: qty, id: db.orders.length + 1}); }

function findUser(id) {
    for (var i = 0; i < db.users.length; i++) {
        if (db.users[i].id == id) return db.users[i];
    }
    return null;
}

function findProduct(id) {
    for (var i = 0; i < db.products.length; i++) {
        if (db.products[i].id == id) return db.products[i];
    }
    return null;
}

function getOrdersForUser(uid) {
    var r = [];
    for (var i = 0; i < db.orders.length; i++) {
        if (db.orders[i].userId == uid) r.push(db.orders[i]);
    }
    return r;
}

function getTotalForUser(uid) {
    var orders = getOrdersForUser(uid);
    var total = 0;
    for (var i = 0; i < orders.length; i++) {
        var p = findProduct(orders[i].productId);
        if (p != null) {
            total = total + p.price * orders[i].qty;
        }
    }
    return total;
}

function report() {
    var s = "";
    for (var i = 0; i < db.users.length; i++) {
        s = s + "User: " + db.users[i].name + " Total: " + getTotalForUser(db.users[i].id) + "\n";
    }
    for (var i = 0; i < db.products.length; i++) {
        var sold = 0;
        for (var j = 0; j < db.orders.length; j++) {
            if (db.orders[j].productId == db.products[i].id) {
                sold = sold + db.orders[j].qty;
            }
        }
        s = s + "Product: " + db.products[i].name + " Sold: " + sold + "\n";
    }
    return s;
}

function clearAll() { db.users = []; db.products = []; db.orders = []; }
