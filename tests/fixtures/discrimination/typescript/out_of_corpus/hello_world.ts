function greet(name: string): string {
  return "Hello, " + name + "!";
}

function greetAll(names: string[]): string[] {
  let results: string[] = [];
  for (let i = 0; i < names.length; i++) {
    results.push(greet(names[i]));
  }
  return results;
}

function main(): void {
  let names = ["Alice", "Bob", "Charlie"];
  let messages = greetAll(names);
  for (let msg of messages) {
    console.log(msg);
  }
}
