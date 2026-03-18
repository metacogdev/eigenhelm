function reverseString(str) {
  var result = "";
  for (var i = str.length - 1; i >= 0; i--) {
    result = result + str[i];
  }
  return result;
}

function countVowels(str) {
  var count = 0;
  var vowels = "aeiouAEIOU";
  for (var i = 0; i < str.length; i++) {
    if (vowels.indexOf(str[i]) !== -1) {
      count++;
    }
  }
  return count;
}

function capitalize(str) {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

module.exports = { reverseString, countVowels, capitalize };
