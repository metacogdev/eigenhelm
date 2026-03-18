type Fn<A, B> = (a: A) => B;

function pipe<A>(value: A): A;
function pipe<A, B>(value: A, f1: Fn<A, B>): B;
function pipe<A, B, C>(value: A, f1: Fn<A, B>, f2: Fn<B, C>): C;
function pipe<A, B, C, D>(value: A, f1: Fn<A, B>, f2: Fn<B, C>, f3: Fn<C, D>): D;
function pipe<A, B, C, D, E>(
  value: A, f1: Fn<A, B>, f2: Fn<B, C>, f3: Fn<C, D>, f4: Fn<D, E>,
): E;
function pipe(value: unknown, ...fns: Fn<unknown, unknown>[]): unknown {
  return fns.reduce((acc, fn) => fn(acc), value);
}

function compose<A, B>(f: Fn<A, B>): Fn<A, B>;
function compose<A, B, C>(f: Fn<A, B>, g: Fn<B, C>): Fn<A, C>;
function compose<A, B, C, D>(f: Fn<A, B>, g: Fn<B, C>, h: Fn<C, D>): Fn<A, D>;
function compose(...fns: Fn<unknown, unknown>[]): Fn<unknown, unknown> {
  return (input: unknown) => fns.reduce((acc, fn) => fn(acc), input);
}

interface Pipeline<Input, Output> {
  then<Next>(fn: Fn<Output, Next>): Pipeline<Input, Next>;
  execute(input: Input): Output;
}

function pipeline<A, B>(first: Fn<A, B>): Pipeline<A, B> {
  function build<I, O>(chain: Fn<I, O>): Pipeline<I, O> {
    return {
      then<Next>(fn: Fn<O, Next>): Pipeline<I, Next> {
        return build((input: I) => fn(chain(input)));
      },
      execute(input: I): O {
        return chain(input);
      },
    };
  }
  return build(first);
}
