function naiveDeepClone(obj) {
  if (obj === null || typeof obj !== "object") {
    return obj;
  }
  if (Array.isArray(obj)) {
    var arrCopy = [];
    for (var i = 0; i < obj.length; i++) {
      arrCopy.push(naiveDeepClone(obj[i]));
    }
    return arrCopy;
  }
  var copy = {};
  var keys = Object.keys(obj);
  for (var i = 0; i < keys.length; i++) {
    copy[keys[i]] = naiveDeepClone(obj[keys[i]]);
  }
  return copy;
}

function shallowMerge(target, source) {
  var result = {};
  var keys = Object.keys(target);
  for (var i = 0; i < keys.length; i++) {
    result[keys[i]] = target[keys[i]];
  }
  keys = Object.keys(source);
  for (var i = 0; i < keys.length; i++) {
    result[keys[i]] = source[keys[i]];
  }
  return result;
}
