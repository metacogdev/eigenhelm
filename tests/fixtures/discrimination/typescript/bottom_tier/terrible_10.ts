// copy-paste calculator methods, magic numbers, any returns
class Calculator {
    history: any[] = [];

    add(a: any, b: any): any { let r: any = (a as number) + (b as number); this.history.push(r); return r; }
    sub(a: any, b: any): any { let r: any = (a as number) - (b as number); this.history.push(r); return r; }
    mul(a: any, b: any): any { let r: any = (a as number) * (b as number); this.history.push(r); return r; }
    div(a: any, b: any): any { let r: any = (a as number) / (b as number); this.history.push(r); return r; }
    mod(a: any, b: any): any { let r: any = (a as number) % (b as number); this.history.push(r); return r; }

    pow(a: any, b: any): any {
        let r: any = 1;
        for (let i: any = 0; i < (b as number); i++) { r = (r as number) * (a as number); }
        this.history.push(r);
        return r;
    }

    sqrt(a: any): any {
        let g: any = (a as number) / 2;
        for (let i: number = 0; i < 100; i++) {
            g = ((g as number) + (a as number) / (g as number)) / 2;
        }
        this.history.push(g);
        return g;
    }

    abs(a: any): any {
        let r: any = (a as number) < 0 ? (a as number) * -1 : a;
        this.history.push(r);
        return r;
    }

    max(a: any, b: any): any {
        let r: any = (a as number) > (b as number) ? a : b;
        this.history.push(r);
        return r;
    }

    min(a: any, b: any): any {
        let r: any = (a as number) < (b as number) ? a : b;
        this.history.push(r);
        return r;
    }

    chain(ops: any[]): any {
        let r: any = 0;
        for (let i: number = 0; i < ops.length; i++) {
            let op: any = ops[i];
            if (op.t == "add") r = this.add(r, op.v);
            else if (op.t == "sub") r = this.sub(r, op.v);
            else if (op.t == "mul") r = this.mul(r, op.v);
            else if (op.t == "div") r = this.div(r, op.v);
            else if (op.t == "mod") r = this.mod(r, op.v);
        }
        return r;
    }

    clearHistory(): void { this.history = []; }
    getHistory(): any { return this.history as any; }
}
