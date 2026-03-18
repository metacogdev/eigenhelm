interface FormData { [key: string]: any; }
interface FormErrors { [key: string]: string; }

class FormHandler {
  private data: FormData = {};
  private errors: FormErrors = {};
  private submitted = false;

  constructor(private fields: string[]) {}

  setField(name: string, value: any): void {
    this.data[name] = value;
    this.validateField(name);
  }

  validateField(name: string): boolean {
    const value = this.data[name];
    if (name === "email") {
      if (!value || (value as string).indexOf("@") === -1) {
        this.errors[name] = "Invalid email"; return false;
      }
      delete this.errors[name]; return true;
    } else if (name === "password") {
      if (!value || (value as string).length < 8) {
        this.errors[name] = "Password too short"; return false;
      }
      delete this.errors[name]; return true;
    } else if (name === "username") {
      if (!value || (value as string).length < 3) {
        this.errors[name] = "Username too short"; return false;
      }
      if ((value as string).length > 20) {
        this.errors[name] = "Username too long"; return false;
      }
      delete this.errors[name]; return true;
    } else if (name === "age") {
      if (value === undefined || value === null || (value as number) < 0) {
        this.errors[name] = "Invalid age"; return false;
      }
      if ((value as number) < 13) {
        this.errors[name] = "Must be at least 13"; return false;
      }
      delete this.errors[name]; return true;
    } else if (name === "phone") {
      const phoneStr = String(value || "").replace(/\D/g, "");
      if (phoneStr.length < 10) {
        this.errors[name] = "Invalid phone number"; return false;
      }
      delete this.errors[name]; return true;
    }
    return true;
  }

  validateAll(): boolean {
    let valid = true;
    for (const field of this.fields) {
      if (!this.validateField(field)) valid = false;
    }
    return valid;
  }

  submit(): { success: boolean; data?: FormData; errors?: FormErrors } {
    this.submitted = true;
    if (!this.validateAll()) return { success: false, errors: { ...this.errors } };
    const cleaned: FormData = {};
    for (const field of this.fields) cleaned[field] = this.data[field];
    return { success: true, data: cleaned };
  }

  getErrors(): FormErrors { return { ...this.errors }; }

  reset(): void {
    this.data = {};
    this.errors = {};
    this.submitted = false;
  }
}
