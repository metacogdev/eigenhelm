// massive switch, string-based dispatch, no enum
let _mode: string = "default";
let _count: number = 0;

function setMode(m: any): void {
    _mode = m as string;
}

function dispatch(action: string, payload: any): any {
    _count++;
    switch(action) {
        case "GET_USER": return {type: "user", data: payload, mode: _mode, count: _count};
        case "SET_USER": return {type: "user", data: payload, mode: _mode, count: _count};
        case "DEL_USER": return {type: "user", data: null, mode: _mode, count: _count};
        case "GET_ITEM": return {type: "item", data: payload, mode: _mode, count: _count};
        case "SET_ITEM": return {type: "item", data: payload, mode: _mode, count: _count};
        case "DEL_ITEM": return {type: "item", data: null, mode: _mode, count: _count};
        case "GET_ORDER": return {type: "order", data: payload, mode: _mode, count: _count};
        case "SET_ORDER": return {type: "order", data: payload, mode: _mode, count: _count};
        case "DEL_ORDER": return {type: "order", data: null, mode: _mode, count: _count};
        case "GET_CART": return {type: "cart", data: payload, mode: _mode, count: _count};
        case "SET_CART": return {type: "cart", data: payload, mode: _mode, count: _count};
        case "DEL_CART": return {type: "cart", data: null, mode: _mode, count: _count};
        case "GET_CONFIG": return {type: "config", data: payload, mode: _mode, count: _count};
        case "SET_CONFIG": return {type: "config", data: payload, mode: _mode, count: _count};
        case "DEL_CONFIG": return {type: "config", data: null, mode: _mode, count: _count};
        case "RESET": _count = 0; _mode = "default"; return {type: "reset", data: null, mode: _mode, count: _count};
        default: return {type: "unknown", data: null, mode: _mode, count: _count};
    }
}

function batchDispatch(actions: any[]): any[] {
    let results: any[] = [];
    for (let i: number = 0; i < actions.length; i++) {
        results.push(dispatch(actions[i].action as string, actions[i].payload as any));
    }
    return results;
}
