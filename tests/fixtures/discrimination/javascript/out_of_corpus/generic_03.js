function createCounter() {
  var count = 0;
  return {
    increment: function () {
      count++;
      return count;
    },
    decrement: function () {
      count--;
      return count;
    },
    getCount: function () {
      return count;
    },
    reset: function () {
      count = 0;
      return count;
    },
  };
}

function countOccurrences(arr, value) {
  var count = 0;
  for (var i = 0; i < arr.length; i++) {
    if (arr[i] === value) {
      count++;
    }
  }
  return count;
}
