// mutable globals, parallel arrays, string-keyed everything
let _names: string[] = [];
let _values: number[] = [];
let _types: string[] = [];
let _flags: boolean[] = [];
let _meta: any[] = [];

function addEntry(n: any, v: any, t: any, f: any, m: any): number {
    _names.push(n as string);
    _values.push(v as number);
    _types.push(t as string);
    _flags.push(f as boolean);
    _meta.push(m as any);
    return _names.length - 1;
}

function getEntry(idx: any): any {
    if ((idx as number) >= 0 && (idx as number) < _names.length) {
        return {
            name: _names[idx as number],
            value: _values[idx as number],
            type: _types[idx as number],
            flag: _flags[idx as number],
            meta: _meta[idx as number]
        } as any;
    }
    return null as any;
}

function findByName(n: any): any {
    for (let i: number = 0; i < _names.length; i++) {
        if (_names[i] == (n as string)) return i as any;
    }
    return -1 as any;
}

function findByType(t: any): any {
    let r: any[] = [];
    for (let i: number = 0; i < _types.length; i++) {
        if (_types[i] == (t as string)) r.push(i as any);
    }
    return r as any;
}

function removeEntry(idx: any): any {
    let nn: string[] = [], nv: number[] = [], nt: string[] = [], nf: boolean[] = [], nm: any[] = [];
    for (let i: number = 0; i < _names.length; i++) {
        if (i != (idx as number)) {
            nn.push(_names[i]); nv.push(_values[i]); nt.push(_types[i]); nf.push(_flags[i]); nm.push(_meta[i]);
        }
    }
    _names = nn; _values = nv; _types = nt; _flags = nf; _meta = nm;
    return true as any;
}

function totalValue(): any {
    let s: any = 0;
    for (let i: any = 0; i < _values.length; i++) { s = (s as number) + _values[i as number]; }
    return s as any;
}
