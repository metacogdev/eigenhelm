type Result<T, E> = Ok<T> | Err<E>;

interface Ok<T> {
  readonly kind: "ok";
  readonly value: T;
}

interface Err<E> {
  readonly kind: "err";
  readonly error: E;
}

function ok<T>(value: T): Ok<T> {
  return { kind: "ok", value };
}

function err<E>(error: E): Err<E> {
  return { kind: "err", error };
}

function map<T, U, E>(result: Result<T, E>, fn: (value: T) => U): Result<U, E> {
  return result.kind === "ok" ? ok(fn(result.value)) : result;
}

function flatMap<T, U, E>(
  result: Result<T, E>,
  fn: (value: T) => Result<U, E>,
): Result<U, E> {
  return result.kind === "ok" ? fn(result.value) : result;
}

function unwrap<T, E>(result: Result<T, E>): T {
  if (result.kind === "ok") {
    return result.value;
  }
  throw new Error(`Tried to unwrap an Err: ${result.error}`);
}

function unwrapOr<T, E>(result: Result<T, E>, fallback: T): T {
  return result.kind === "ok" ? result.value : fallback;
}

function fromThrowable<T>(fn: () => T): Result<T, Error> {
  try {
    return ok(fn());
  } catch (e) {
    return err(e instanceof Error ? e : new Error(String(e)));
  }
}

function combine<T, E>(results: Result<T, E>[]): Result<T[], E> {
  const values: T[] = [];
  for (const result of results) {
    if (result.kind === "err") {
      return result;
    }
    values.push(result.value);
  }
  return ok(values);
}
