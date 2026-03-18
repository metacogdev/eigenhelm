function reverseString(str) {
  var result = "";
  for (var i = str.length - 1; i >= 0; i--) {
    result += str[i];
  }
  return result;
}

function isPalindrome(str) {
  var cleaned = str.toLowerCase().replace(/[^a-z0-9]/g, "");
  return cleaned === reverseString(cleaned);
}

function countVowels(str) {
  var vowels = "aeiouAEIOU";
  var count = 0;
  for (var i = 0; i < str.length; i++) {
    if (vowels.indexOf(str[i]) !== -1) {
      count++;
    }
  }
  return count;
}

function truncateString(str, maxLen) {
  if (str.length <= maxLen) {
    return str;
  }
  return str.substring(0, maxLen) + "...";
}
