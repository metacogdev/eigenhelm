interface FormField {
  name: string;
  value: string;
  required: boolean;
}

function validateRequired(fields: FormField[]): string[] {
  const errors: string[] = [];
  for (const field of fields) {
    if (field.required && field.value.trim() === "") {
      errors.push(field.name + " is required");
    }
  }
  return errors;
}

function validateMinLength(value: string, min: number): boolean {
  return value.length >= min;
}

function validateMaxLength(value: string, max: number): boolean {
  return value.length <= max;
}

function validateEmail(email: string): boolean {
  if (email.indexOf("@") === -1) {
    return false;
  }
  const parts = email.split("@");
  if (parts.length !== 2) {
    return false;
  }
  return parts[1].indexOf(".") !== -1;
}

function validateForm(fields: FormField[]): { valid: boolean; errors: string[] } {
  const errors = validateRequired(fields);
  return { valid: errors.length === 0, errors: errors };
}
