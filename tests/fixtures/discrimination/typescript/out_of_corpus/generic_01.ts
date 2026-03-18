interface Animal {
  name: string;
  sound: string;
  legs: number;
}

function describeAnimal(animal: Animal): string {
  return animal.name + " says " + animal.sound + " and has " + animal.legs + " legs";
}

function filterByLegs(animals: Animal[], legCount: number): Animal[] {
  const result: Animal[] = [];
  for (let i = 0; i < animals.length; i++) {
    if (animals[i].legs === legCount) {
      result.push(animals[i]);
    }
  }
  return result;
}

function getAnimalNames(animals: Animal[]): string[] {
  const names: string[] = [];
  for (const a of animals) {
    names.push(a.name);
  }
  return names;
}
