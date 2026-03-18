// manual serialization, no interfaces, string building
function serialize(obj: any): string {
    let s: string = "{";
    let keys: any = Object.keys(obj as any);
    for (let i: number = 0; i < keys.length; i++) {
        if (i > 0) s = s + ",";
        let k: any = keys[i];
        let v: any = (obj as any)[k as string];
        s = s + '"' + (k as string) + '":';
        if (typeof v == "string") {
            s = s + '"' + (v as string) + '"';
        } else if (typeof v == "number") {
            s = s + String(v as number);
        } else if (typeof v == "boolean") {
            s = s + String(v as boolean);
        } else if (v == null) {
            s = s + "null";
        } else if (Array.isArray(v)) {
            s = s + "[";
            for (let j: number = 0; j < (v as any[]).length; j++) {
                if (j > 0) s = s + ",";
                if (typeof (v as any[])[j] == "string") {
                    s = s + '"' + (v as any[])[j] + '"';
                } else if (typeof (v as any[])[j] == "number") {
                    s = s + String((v as any[])[j]);
                } else {
                    s = s + "null";
                }
            }
            s = s + "]";
        } else {
            s = s + serialize(v);
        }
    }
    s = s + "}";
    return s;
}

function deserialize(s: string): any {
    try {
        return JSON.parse(s) as any;
    } catch(e) {
        return null as any;
    }
}

function clone(obj: any): any {
    return deserialize(serialize(obj)) as any;
}

function merge(a: any, b: any): any {
    let r: any = clone(a);
    let keys: any = Object.keys(b as any);
    for (let i: number = 0; i < keys.length; i++) {
        (r as any)[keys[i] as string] = (b as any)[keys[i] as string];
    }
    return r as any;
}
