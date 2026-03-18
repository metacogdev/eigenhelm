function validateEmail(email) {
  if (email.indexOf("@") === -1) {
    return false;
  }
  var parts = email.split("@");
  if (parts.length !== 2) {
    return false;
  }
  if (parts[0].length === 0 || parts[1].length === 0) {
    return false;
  }
  if (parts[1].indexOf(".") === -1) {
    return false;
  }
  return true;
}

function validateAge(age) {
  if (typeof age !== "number") {
    return false;
  }
  if (age < 0 || age > 150) {
    return false;
  }
  return true;
}

function validateUsername(name) {
  if (name.length < 3 || name.length > 20) {
    return false;
  }
  for (var i = 0; i < name.length; i++) {
    var ch = name[i];
    if (!(ch >= "a" && ch <= "z") && !(ch >= "0" && ch <= "9") && ch !== "_") {
      return false;
    }
  }
  return true;
}
