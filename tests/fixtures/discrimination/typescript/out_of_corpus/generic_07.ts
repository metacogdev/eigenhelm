function reverseString(s: string): string {
  let result = "";
  for (let i = s.length - 1; i >= 0; i--) {
    result += s[i];
  }
  return result;
}

function countWords(s: string): number {
  const trimmed = s.trim();
  if (trimmed === "") return 0;
  return trimmed.split(/\s+/).length;
}

function repeatString(s: string, times: number): string {
  let result = "";
  for (let i = 0; i < times; i++) {
    result += s;
  }
  return result;
}

function isPalindrome(s: string): boolean {
  const cleaned = s.toLowerCase().replace(/[^a-z0-9]/g, "");
  return cleaned === reverseString(cleaned);
}

function truncate(s: string, maxLen: number): string {
  if (s.length <= maxLen) return s;
  return s.substring(0, maxLen) + "...";
}
