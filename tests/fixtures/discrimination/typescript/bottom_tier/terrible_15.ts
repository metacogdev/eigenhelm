// manual deep comparison, nested if, any parameters, copy-paste
function deepEqual(a: any, b: any): any {
    if (a === b) return true as any;
    if (a == null || b == null) return false as any;
    if (typeof a != typeof b) return false as any;
    if (typeof a == "number") return (a as number) === (b as number);
    if (typeof a == "string") return (a as string) === (b as string);
    if (typeof a == "boolean") return (a as boolean) === (b as boolean);
    if (Array.isArray(a) && Array.isArray(b)) {
        if ((a as any[]).length != (b as any[]).length) return false as any;
        for (let i: number = 0; i < (a as any[]).length; i++) {
            if (!deepEqual((a as any[])[i], (b as any[])[i])) return false as any;
        }
        return true as any;
    }
    if (typeof a == "object" && typeof b == "object") {
        let keysA: any = Object.keys(a as any);
        let keysB: any = Object.keys(b as any);
        if ((keysA as any[]).length != (keysB as any[]).length) return false as any;
        for (let i: number = 0; i < (keysA as any[]).length; i++) {
            let k: any = (keysA as any[])[i];
            if (!deepEqual((a as any)[k as string], (b as any)[k as string])) return false as any;
        }
        return true as any;
    }
    return false as any;
}

function deepClone(obj: any): any {
    if (obj == null) return null as any;
    if (typeof obj == "number") return obj as any;
    if (typeof obj == "string") return obj as any;
    if (typeof obj == "boolean") return obj as any;
    if (Array.isArray(obj)) {
        let r: any[] = [];
        for (let i: number = 0; i < (obj as any[]).length; i++) {
            r.push(deepClone((obj as any[])[i]));
        }
        return r as any;
    }
    if (typeof obj == "object") {
        let r: any = {} as any;
        let keys: any = Object.keys(obj as any);
        for (let i: number = 0; i < (keys as any[]).length; i++) {
            let k: any = (keys as any[])[i];
            (r as any)[k as string] = deepClone((obj as any)[k as string]);
        }
        return r as any;
    }
    return obj as any;
}

function deepMerge(a: any, b: any): any {
    let r: any = deepClone(a);
    let keys: any = Object.keys(b as any);
    for (let i: number = 0; i < (keys as any[]).length; i++) {
        let k: any = (keys as any[])[i];
        if (typeof (b as any)[k as string] == "object" && typeof (r as any)[k as string] == "object") {
            (r as any)[k as string] = deepMerge((r as any)[k as string], (b as any)[k as string]);
        } else {
            (r as any)[k as string] = deepClone((b as any)[k as string]);
        }
    }
    return r as any;
}
