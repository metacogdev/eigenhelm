function formatCurrency(amount) {
  return "$" + amount.toFixed(2);
}

function padLeft(str, length, char) {
  while (str.length < length) {
    str = char + str;
  }
  return str;
}

function formatDate(year, month, day) {
  var m = padLeft(String(month), 2, "0");
  var d = padLeft(String(day), 2, "0");
  return year + "-" + m + "-" + d;
}

function repeatString(str, times) {
  var result = "";
  for (var i = 0; i < times; i++) {
    result += str;
  }
  return result;
}

function capitalizeFirst(str) {
  if (str.length === 0) return str;
  return str[0].toUpperCase() + str.slice(1);
}

function camelToSnake(str) {
  var result = "";
  for (var i = 0; i < str.length; i++) {
    if (str[i] >= "A" && str[i] <= "Z") {
      result += "_" + str[i].toLowerCase();
    } else {
      result += str[i];
    }
  }
  return result;
}
