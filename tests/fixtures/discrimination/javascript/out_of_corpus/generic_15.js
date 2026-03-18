function Stack() {
  this.items = [];
}

Stack.prototype.push = function (item) {
  this.items.push(item);
};

Stack.prototype.pop = function () {
  if (this.items.length === 0) {
    return undefined;
  }
  return this.items.pop();
};

Stack.prototype.peek = function () {
  if (this.items.length === 0) {
    return undefined;
  }
  return this.items[this.items.length - 1];
};

Stack.prototype.isEmpty = function () {
  return this.items.length === 0;
};

Stack.prototype.size = function () {
  return this.items.length;
};

Stack.prototype.toArray = function () {
  return this.items.slice();
};

Stack.prototype.clear = function () {
  this.items = [];
};
