interface Student {
  name: string;
  grade: number;
}

function getPassingStudents(students: Student[], threshold: number): Student[] {
  const result: Student[] = [];
  for (const s of students) {
    if (s.grade >= threshold) {
      result.push(s);
    }
  }
  return result;
}

function getClassAverage(students: Student[]): number {
  if (students.length === 0) return 0;
  let total = 0;
  for (const s of students) {
    total += s.grade;
  }
  return total / students.length;
}

function getTopStudent(students: Student[]): Student | null {
  if (students.length === 0) return null;
  let best = students[0];
  for (let i = 1; i < students.length; i++) {
    if (students[i].grade > best.grade) {
      best = students[i];
    }
  }
  return best;
}

function sortByGrade(students: Student[]): Student[] {
  const result = students.slice();
  result.sort((a, b) => b.grade - a.grade);
  return result;
}
