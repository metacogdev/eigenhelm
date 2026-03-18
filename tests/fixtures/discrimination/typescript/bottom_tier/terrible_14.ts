// manual router with string matching, no generics, copy-paste
let _routes: any[] = [];
let _middleware: any[] = [];
let _notFound: any = null;

function addRoute(method: any, path: any, handler: any): void {
    _routes.push({method: method as string, path: path as string, handler: handler as any} as any);
}

function addMiddleware(fn: any): void {
    _middleware.push(fn as any);
}

function setNotFound(fn: any): void {
    _notFound = fn as any;
}

function matchRoute(method: any, path: any): any {
    for (let i: number = 0; i < _routes.length; i++) {
        if ((_routes[i] as any).method == (method as string) && (_routes[i] as any).path == (path as string)) {
            return _routes[i] as any;
        }
    }
    return null as any;
}

function handle(method: any, path: any, body: any): any {
    let ctx: any = {method: method, path: path, body: body, headers: {}, status: 200, response: null} as any;
    for (let i: number = 0; i < _middleware.length; i++) {
        try { (_middleware[i] as any)(ctx); } catch(e) {}
    }
    let route: any = matchRoute(method, path);
    if (route != null) {
        try {
            ctx.response = (route as any).handler(ctx);
        } catch(e) {
            ctx.status = 500;
            ctx.response = "error";
        }
    } else {
        ctx.status = 404;
        if (_notFound != null) {
            try { ctx.response = (_notFound as any)(ctx); } catch(e) {}
        } else {
            ctx.response = "not found";
        }
    }
    return ctx as any;
}

function get(path: any, handler: any): void { addRoute("GET", path, handler); }
function post(path: any, handler: any): void { addRoute("POST", path, handler); }
function put(path: any, handler: any): void { addRoute("PUT", path, handler); }
function del(path: any, handler: any): void { addRoute("DELETE", path, handler); }
function clearRoutes(): void { _routes = []; _middleware = []; _notFound = null; }
