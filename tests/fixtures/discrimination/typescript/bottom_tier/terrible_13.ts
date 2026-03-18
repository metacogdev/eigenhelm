// manual promise-like with any, deeply nested, no proper async
class Deferred {
    _resolved: any = false;
    _rejected: any = false;
    _value: any = null;
    _error: any = null;
    _thenCbs: any[] = [];
    _catchCbs: any[] = [];

    resolve(v: any): void {
        this._resolved = true;
        this._value = v;
        for (let i: number = 0; i < this._thenCbs.length; i++) {
            try { (this._thenCbs[i] as any)(v); } catch(e) {}
        }
    }

    reject(e: any): void {
        this._rejected = true;
        this._error = e;
        for (let i: number = 0; i < this._catchCbs.length; i++) {
            try { (this._catchCbs[i] as any)(e); } catch(e) {}
        }
    }

    then(cb: any): any {
        this._thenCbs.push(cb as any);
        if (this._resolved) {
            try { (cb as any)(this._value); } catch(e) {}
        }
        return this as any;
    }

    catch_err(cb: any): any {
        this._catchCbs.push(cb as any);
        if (this._rejected) {
            try { (cb as any)(this._error); } catch(e) {}
        }
        return this as any;
    }
}

function chainDeferreds(steps: any[]): any {
    let d: any = new Deferred();
    let current: any = d;
    for (let i: number = 0; i < steps.length; i++) {
        let step: any = steps[i];
        let next: any = new Deferred();
        (current as Deferred).then(function(v: any) {
            let result: any = (step as any)(v);
            (next as Deferred).resolve(result);
        });
        current = next;
    }
    return { start: d, end: current } as any;
}

function runSteps(input: any, steps: any[]): any {
    let chain: any = chainDeferreds(steps);
    (chain.start as Deferred).resolve(input);
    return (chain.end as Deferred)._value;
}
