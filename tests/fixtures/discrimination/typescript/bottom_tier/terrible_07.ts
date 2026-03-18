// god class that does everything, any params, ignored errors
class AppManager {
    users: any[] = [];
    products: any[] = [];
    orders: any[] = [];
    logs: any[] = [];
    config: any = {};

    addUser(a: any, b: any, c: any): any { try { this.users.push({a, b, c}); } catch(e) {} return this; }
    addProduct(a: any, b: any, c: any): any { try { this.products.push({a, b, c}); } catch(e) {} return this; }
    addOrder(a: any, b: any, c: any): any { try { this.orders.push({a, b, c}); } catch(e) {} return this; }
    addLog(a: any): any { try { this.logs.push(a); } catch(e) {} return this; }

    findUser(id: any): any {
        for (let i: any = 0; i < this.users.length; i++) {
            if ((this.users[i] as any).a == id) return this.users[i] as any;
        }
        return null as any;
    }

    findProduct(id: any): any {
        for (let i: any = 0; i < this.products.length; i++) {
            if ((this.products[i] as any).a == id) return this.products[i] as any;
        }
        return null as any;
    }

    findOrder(id: any): any {
        for (let i: any = 0; i < this.orders.length; i++) {
            if ((this.orders[i] as any).a == id) return this.orders[i] as any;
        }
        return null as any;
    }

    countUsers(): any { return this.users.length as any; }
    countProducts(): any { return this.products.length as any; }
    countOrders(): any { return this.orders.length as any; }
    countLogs(): any { return this.logs.length as any; }

    clearUsers(): any { this.users = []; return this; }
    clearProducts(): any { this.products = []; return this; }
    clearOrders(): any { this.orders = []; return this; }
    clearLogs(): any { this.logs = []; return this; }
    clearAll(): any { this.users = []; this.products = []; this.orders = []; this.logs = []; this.config = {}; return this; }

    setConfig(k: any, v: any): any { this.config[k as string] = v; return this; }
    getConfig(k: any): any { return this.config[k as string] as any; }

    report(): any {
        let s: any = "";
        s = s + "Users: " + this.users.length + "\n";
        s = s + "Products: " + this.products.length + "\n";
        s = s + "Orders: " + this.orders.length + "\n";
        s = s + "Logs: " + this.logs.length + "\n";
        return s as any;
    }
}
