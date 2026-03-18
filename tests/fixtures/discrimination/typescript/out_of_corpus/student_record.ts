interface Student {
  name: string;
  grade: number;
}

let students: Student[] = [];

function addStudent(name: string, grade: number): void {
  students.push({ name: name, grade: grade });
}

function getAverage(): number {
  let sum = 0;
  for (let s of students) {
    sum += s.grade;
  }
  return sum / students.length;
}

function findStudent(name: string): Student | undefined {
  for (let s of students) {
    if (s.name === name) {
      return s;
    }
  }
  return undefined;
}
