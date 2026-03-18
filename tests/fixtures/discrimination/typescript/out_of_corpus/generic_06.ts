function sum(numbers: number[]): number {
  let total = 0;
  for (const n of numbers) {
    total += n;
  }
  return total;
}

function average(numbers: number[]): number {
  if (numbers.length === 0) return 0;
  return sum(numbers) / numbers.length;
}

function median(numbers: number[]): number {
  if (numbers.length === 0) return 0;
  const sorted = numbers.slice().sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  if (sorted.length % 2 === 0) {
    return (sorted[mid - 1] + sorted[mid]) / 2;
  }
  return sorted[mid];
}

function mode(numbers: number[]): number {
  const counts: { [key: number]: number } = {};
  for (const n of numbers) {
    counts[n] = (counts[n] || 0) + 1;
  }
  let maxCount = 0;
  let result = numbers[0];
  for (const key in counts) {
    if (counts[key] > maxCount) {
      maxCount = counts[key];
      result = Number(key);
    }
  }
  return result;
}

function range(numbers: number[]): number {
  if (numbers.length === 0) return 0;
  let min = numbers[0];
  let max = numbers[0];
  for (const n of numbers) {
    if (n < min) min = n;
    if (n > max) max = n;
  }
  return max - min;
}
