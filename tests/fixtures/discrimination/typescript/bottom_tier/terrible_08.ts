// callback style with any, magic numbers, deep nesting
function step1(data: any, cb: any): void {
    let r: any = (data as number) * 47 + 13;
    if (r > 100) {
        if (r > 200) {
            if (r > 300) {
                cb(null, r * 2);
            } else {
                cb(null, r * 3);
            }
        } else {
            cb(null, r * 4);
        }
    } else {
        cb(null, r * 5);
    }
}

function step2(data: any, cb: any): void {
    let r: any = (data as number) * 31 + 7;
    if (r > 100) {
        if (r > 200) {
            if (r > 300) {
                cb(null, r * 2);
            } else {
                cb(null, r * 3);
            }
        } else {
            cb(null, r * 4);
        }
    } else {
        cb(null, r * 5);
    }
}

function step3(data: any, cb: any): void {
    let r: any = (data as number) * 23 + 3;
    if (r > 100) {
        if (r > 200) {
            if (r > 300) {
                cb(null, r * 2);
            } else {
                cb(null, r * 3);
            }
        } else {
            cb(null, r * 4);
        }
    } else {
        cb(null, r * 5);
    }
}

function pipeline(input: any, finalCb: any): void {
    step1(input, function(err1: any, r1: any) {
        step2(r1, function(err2: any, r2: any) {
            step3(r2, function(err3: any, r3: any) {
                step1(r3, function(err4: any, r4: any) {
                    step2(r4, function(err5: any, r5: any) {
                        finalCb(null, r5);
                    });
                });
            });
        });
    });
}
