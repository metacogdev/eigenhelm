function bubbleSort(arr) {
  var result = arr.slice();
  var n = result.length;
  for (var i = 0; i < n; i++) {
    for (var j = 0; j < n - i - 1; j++) {
      if (result[j] > result[j + 1]) {
        var temp = result[j];
        result[j] = result[j + 1];
        result[j + 1] = temp;
      }
    }
  }
  return result;
}

function binarySearch(arr, target) {
  var low = 0;
  var high = arr.length - 1;
  while (low <= high) {
    var mid = Math.floor((low + high) / 2);
    if (arr[mid] === target) {
      return mid;
    } else if (arr[mid] < target) {
      low = mid + 1;
    } else {
      high = mid - 1;
    }
  }
  return -1;
}
