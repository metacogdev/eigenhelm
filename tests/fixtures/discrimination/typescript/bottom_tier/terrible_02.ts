// class with 20 similar methods, mutable globals, ignored errors
let ERROR_LOG: any[] = [];
let CALL_COUNT: number = 0;

class DataProcessor {
    data: any;
    constructor() { this.data = []; }
    add1(x: any) { try { this.data.push(x * 1 + 0); CALL_COUNT++; } catch(e) {} }
    add2(x: any) { try { this.data.push(x * 1 + 1); CALL_COUNT++; } catch(e) {} }
    add3(x: any) { try { this.data.push(x * 1 + 2); CALL_COUNT++; } catch(e) {} }
    add4(x: any) { try { this.data.push(x * 1 + 3); CALL_COUNT++; } catch(e) {} }
    add5(x: any) { try { this.data.push(x * 1 + 4); CALL_COUNT++; } catch(e) {} }
    add6(x: any) { try { this.data.push(x * 1 + 5); CALL_COUNT++; } catch(e) {} }
    add7(x: any) { try { this.data.push(x * 1 + 6); CALL_COUNT++; } catch(e) {} }
    add8(x: any) { try { this.data.push(x * 1 + 7); CALL_COUNT++; } catch(e) {} }
    add9(x: any) { try { this.data.push(x * 1 + 8); CALL_COUNT++; } catch(e) {} }
    add10(x: any) { try { this.data.push(x * 1 + 9); CALL_COUNT++; } catch(e) {} }
    add11(x: any) { try { this.data.push(x * 2 + 0); CALL_COUNT++; } catch(e) {} }
    add12(x: any) { try { this.data.push(x * 2 + 1); CALL_COUNT++; } catch(e) {} }
    add13(x: any) { try { this.data.push(x * 2 + 2); CALL_COUNT++; } catch(e) {} }
    add14(x: any) { try { this.data.push(x * 2 + 3); CALL_COUNT++; } catch(e) {} }
    add15(x: any) { try { this.data.push(x * 2 + 4); CALL_COUNT++; } catch(e) {} }
    add16(x: any) { try { this.data.push(x * 2 + 5); CALL_COUNT++; } catch(e) {} }
    add17(x: any) { try { this.data.push(x * 2 + 6); CALL_COUNT++; } catch(e) {} }
    add18(x: any) { try { this.data.push(x * 2 + 7); CALL_COUNT++; } catch(e) {} }
    add19(x: any) { try { this.data.push(x * 2 + 8); CALL_COUNT++; } catch(e) {} }
    add20(x: any) { try { this.data.push(x * 2 + 9); CALL_COUNT++; } catch(e) {} }
    runAll(x: any) {
        this.add1(x); this.add2(x); this.add3(x); this.add4(x); this.add5(x);
        this.add6(x); this.add7(x); this.add8(x); this.add9(x); this.add10(x);
        this.add11(x); this.add12(x); this.add13(x); this.add14(x); this.add15(x);
        this.add16(x); this.add17(x); this.add18(x); this.add19(x); this.add20(x);
        return this.data;
    }
    getSum(): any {
        let s: any = 0;
        for (let i: any = 0; i < this.data.length; i++) { s = s + this.data[i]; }
        return s;
    }
}
