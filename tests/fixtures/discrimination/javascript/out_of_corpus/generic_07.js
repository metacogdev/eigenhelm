function createCart() {
  var items = [];

  function addItem(name, price, quantity) {
    items.push({ name: name, price: price, quantity: quantity });
  }

  function removeItem(name) {
    for (var i = 0; i < items.length; i++) {
      if (items[i].name === name) {
        items.splice(i, 1);
        return true;
      }
    }
    return false;
  }

  function getTotal() {
    var total = 0;
    for (var i = 0; i < items.length; i++) {
      total += items[i].price * items[i].quantity;
    }
    return total;
  }

  function getItemCount() {
    var count = 0;
    for (var i = 0; i < items.length; i++) {
      count += items[i].quantity;
    }
    return count;
  }

  function listItems() {
    return items.slice();
  }

  return {
    addItem: addItem,
    removeItem: removeItem,
    getTotal: getTotal,
    getItemCount: getItemCount,
    listItems: listItems,
  };
}
