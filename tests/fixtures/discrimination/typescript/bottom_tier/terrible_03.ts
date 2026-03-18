// type assertions galore, reimplemented stdlib, no generics
function myIncludes(arr: any, val: any): any {
    for (let i: number = 0; i < (arr as any[]).length; i++) {
        if ((arr as any[])[i] === val) return true as any;
    }
    return false as any;
}

function myIndexOf(arr: any, val: any): any {
    for (let i: number = 0; i < (arr as any[]).length; i++) {
        if ((arr as any[])[i] === val) return i as any;
    }
    return -1 as any;
}

function mySlice(arr: any, start: any, end: any): any {
    let r: any = [];
    for (let i: any = start as number; i < (end as number); i++) {
        (r as any[]).push((arr as any[])[i as number]);
    }
    return r as any;
}

function myConcat(a: any, b: any): any {
    let r: any = [];
    for (let i: any = 0; i < (a as any[]).length; i++) { (r as any[]).push((a as any[])[i]); }
    for (let i: any = 0; i < (b as any[]).length; i++) { (r as any[]).push((b as any[])[i]); }
    return r as any;
}

function myReverse(arr: any): any {
    let r: any = [];
    for (let i: any = (arr as any[]).length - 1; i >= 0; i--) {
        (r as any[]).push((arr as any[])[i as number]);
    }
    return r as any;
}

function myJoin(arr: any, sep: any): any {
    let s: any = "";
    for (let i: any = 0; i < (arr as any[]).length; i++) {
        if ((i as number) > 0) s = (s as string) + (sep as string);
        s = (s as string) + String((arr as any[])[i as number]);
    }
    return s as any;
}

function myFlat(arr: any): any {
    let r: any = [];
    for (let i: any = 0; i < (arr as any[]).length; i++) {
        let item: any = (arr as any[])[i as number];
        if (Array.isArray(item)) {
            for (let j: any = 0; j < (item as any[]).length; j++) {
                (r as any[]).push((item as any[])[j as number]);
            }
        } else {
            (r as any[]).push(item);
        }
    }
    return r as any;
}
