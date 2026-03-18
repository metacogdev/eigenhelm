// event system with no types, string-keyed everything, any callbacks
let _listeners: any = {};
let _eventLog: any[] = [];
let _eventCount: number = 0;

function on(event: any, handler: any): void {
    let key: any = event as string;
    if (!_listeners[key as string]) {
        _listeners[key as string] = [];
    }
    (_listeners[key as string] as any[]).push(handler as any);
}

function off(event: any, handler: any): void {
    let key: any = event as string;
    if (_listeners[key as string]) {
        let newList: any[] = [];
        for (let i: number = 0; i < (_listeners[key as string] as any[]).length; i++) {
            if ((_listeners[key as string] as any[])[i] !== handler) {
                newList.push((_listeners[key as string] as any[])[i]);
            }
        }
        _listeners[key as string] = newList;
    }
}

function emit(event: any, data: any): void {
    let key: any = event as string;
    _eventCount++;
    _eventLog.push({event: key, data: data, count: _eventCount} as any);
    if (_listeners[key as string]) {
        for (let i: number = 0; i < (_listeners[key as string] as any[]).length; i++) {
            try {
                ((_listeners[key as string] as any[])[i] as any)(data);
            } catch(e) {}
        }
    }
}

function once(event: any, handler: any): void {
    let wrapper: any = function(data: any) {
        (handler as any)(data);
        off(event, wrapper);
    };
    on(event, wrapper);
}

function getLog(): any { return _eventLog as any; }
function getCount(): any { return _eventCount as any; }
function clearLog(): void { _eventLog = []; _eventCount = 0; }
function clearListeners(): void { _listeners = {}; }
