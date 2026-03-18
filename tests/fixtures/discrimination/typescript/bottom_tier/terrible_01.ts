// any everywhere, type assertions, no proper typing
let globalState: any = {};
let globalCache: any = {};
let globalCounter: any = 0;

function processData(data: any): any {
    let result: any = {};
    result.items = [];
    result.count = 0;
    result.total = 0;
    for (let i: any = 0; i < data.length; i++) {
        let item: any = data[i];
        let processed: any = {} as any;
        processed.id = item.id as any;
        processed.name = (item as any).name;
        processed.value = (item as any).value * 2;
        processed.score = ((item as any).score as any) + 10;
        processed.flag = !!(item as any).active;
        result.items.push(processed);
        result.count = result.count + 1;
        result.total = result.total + processed.value;
    }
    globalState = result;
    globalCounter = globalCounter + 1;
    return result;
}

function transform(input: any): any {
    let output: any = [];
    if ((input as any).items) {
        for (let i: any = 0; i < (input as any).items.length; i++) {
            let x: any = (input as any).items[i];
            output.push({a: x.id, b: x.name, c: x.value, d: x.score, e: x.flag} as any);
        }
    }
    return output as any;
}

function cache(key: any, value: any): any {
    globalCache[key as string] = value;
    return globalCache;
}

function getCache(key: any): any {
    return globalCache[key as string] as any;
}

function clearCache(): any {
    globalCache = {} as any;
    return globalCache;
}
