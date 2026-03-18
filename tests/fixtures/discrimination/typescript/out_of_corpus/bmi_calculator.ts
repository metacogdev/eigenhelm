function calculateBmi(weight: number, height: number): number {
  return weight / (height * height);
}

function getCategory(bmi: number): string {
  if (bmi < 18.5) {
    return "underweight";
  } else if (bmi < 25) {
    return "normal";
  } else if (bmi < 30) {
    return "overweight";
  } else {
    return "obese";
  }
}

function printReport(name: string, weight: number, height: number): void {
  let bmi = calculateBmi(weight, height);
  let category = getCategory(bmi);
  console.log(name + ": BMI=" + bmi.toFixed(1) + " (" + category + ")");
}
