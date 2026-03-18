type SchemaType = "string" | "number" | "boolean" | "object" | "array";

interface SchemaField {
  type: SchemaType;
  required?: boolean;
  minLength?: number;
  maxLength?: number;
  min?: number;
  max?: number;
  pattern?: string;
  fields?: Record<string, SchemaField>;
  items?: SchemaField;
}

interface ValidationError { path: string; message: string; }

function validateField(value: unknown, schema: SchemaField, path: string): ValidationError[] {
  const errors: ValidationError[] = [];
  if (value === undefined || value === null) {
    if (schema.required) errors.push({ path, message: "Field is required" });
    return errors;
  }

  if (schema.type === "string") {
    if (typeof value !== "string") return [{ path, message: `Expected string, got ${typeof value}` }];
    if (schema.minLength !== undefined && value.length < schema.minLength)
      errors.push({ path, message: `Minimum length is ${schema.minLength}` });
    if (schema.maxLength !== undefined && value.length > schema.maxLength)
      errors.push({ path, message: `Maximum length is ${schema.maxLength}` });
    if (schema.pattern && !new RegExp(schema.pattern).test(value))
      errors.push({ path, message: `Does not match pattern ${schema.pattern}` });
  } else if (schema.type === "number") {
    if (typeof value !== "number" || Number.isNaN(value))
      return [{ path, message: `Expected number, got ${typeof value}` }];
    if (schema.min !== undefined && value < schema.min)
      errors.push({ path, message: `Minimum value is ${schema.min}` });
    if (schema.max !== undefined && value > schema.max)
      errors.push({ path, message: `Maximum value is ${schema.max}` });
  } else if (schema.type === "boolean") {
    if (typeof value !== "boolean")
      errors.push({ path, message: `Expected boolean, got ${typeof value}` });
  } else if (schema.type === "object") {
    if (typeof value !== "object" || Array.isArray(value))
      return [{ path, message: "Expected object" }];
    if (schema.fields) {
      const obj = value as Record<string, unknown>;
      for (const [key, fieldSchema] of Object.entries(schema.fields))
        errors.push(...validateField(obj[key], fieldSchema, `${path}.${key}`));
    }
  } else if (schema.type === "array") {
    if (!Array.isArray(value)) return [{ path, message: "Expected array" }];
    if (schema.items) {
      for (let i = 0; i < value.length; i++)
        errors.push(...validateField(value[i], schema.items, `${path}[${i}]`));
    }
  }
  return errors;
}

function validate(data: unknown, schema: Record<string, SchemaField>) {
  const errors: ValidationError[] = [];
  const obj = (typeof data === "object" && data !== null ? data : {}) as Record<string, unknown>;
  for (const [key, fieldSchema] of Object.entries(schema))
    errors.push(...validateField(obj[key], fieldSchema, key));
  return { valid: errors.length === 0, errors };
}
