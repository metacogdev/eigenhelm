function groupBy(arr, key) {
  var result = {};
  for (var i = 0; i < arr.length; i++) {
    var k = arr[i][key];
    if (!result[k]) {
      result[k] = [];
    }
    result[k].push(arr[i]);
  }
  return result;
}

function pluck(arr, key) {
  var result = [];
  for (var i = 0; i < arr.length; i++) {
    result.push(arr[i][key]);
  }
  return result;
}

function filterBy(arr, key, value) {
  var result = [];
  for (var i = 0; i < arr.length; i++) {
    if (arr[i][key] === value) {
      result.push(arr[i]);
    }
  }
  return result;
}

function sortBy(arr, key) {
  var result = arr.slice();
  for (var i = 0; i < result.length; i++) {
    for (var j = i + 1; j < result.length; j++) {
      if (result[i][key] > result[j][key]) {
        var temp = result[i];
        result[i] = result[j];
        result[j] = temp;
      }
    }
  }
  return result;
}
