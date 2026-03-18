var users = [];

function addUser(name, age) {
  var user = { name: name, age: age };
  users.push(user);
  console.log("Added user: " + name);
}

function removeUser(name) {
  for (var i = 0; i < users.length; i++) {
    if (users[i].name === name) {
      users.splice(i, 1);
      console.log("Removed: " + name);
      return;
    }
  }
  console.log("User not found");
}

function listUsers() {
  for (var i = 0; i < users.length; i++) {
    console.log(users[i].name + " - " + users[i].age);
  }
}

module.exports = { addUser, removeUser, listUsers };
