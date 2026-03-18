// string template builder with massive duplication
function buildEmail(to: any, from: any, subject: any, body: any, cc: any): any {
    let h: any = "";
    h = h + "From: " + (from as string) + "\n";
    h = h + "To: " + (to as string) + "\n";
    h = h + "Subject: " + (subject as string) + "\n";
    if (cc != null && cc != undefined) {
        h = h + "CC: " + (cc as string) + "\n";
    }
    h = h + "\n";
    h = h + (body as string);
    return h as any;
}

function buildReport(title: any, sections: any): any {
    let h: any = "";
    h = h + "=".repeat(60) + "\n";
    h = h + " ".repeat(20) + (title as string) + "\n";
    h = h + "=".repeat(60) + "\n";
    h = h + "\n";
    for (let i: number = 0; i < (sections as any[]).length; i++) {
        h = h + "-".repeat(40) + "\n";
        h = h + (sections as any[])[i].title + "\n";
        h = h + "-".repeat(40) + "\n";
        h = h + (sections as any[])[i].content + "\n";
        h = h + "\n";
    }
    h = h + "=".repeat(60) + "\n";
    return h as any;
}

function buildTable(headers: any, rows: any): any {
    let h: any = "";
    h = h + "|";
    for (let i: number = 0; i < (headers as any[]).length; i++) {
        h = h + " " + (headers as any[])[i] + " |";
    }
    h = h + "\n";
    h = h + "|";
    for (let i: number = 0; i < (headers as any[]).length; i++) {
        h = h + "------|";
    }
    h = h + "\n";
    for (let i: number = 0; i < (rows as any[]).length; i++) {
        h = h + "|";
        for (let j: number = 0; j < (rows as any[])[i].length; j++) {
            h = h + " " + (rows as any[])[i][j] + " |";
        }
        h = h + "\n";
    }
    return h as any;
}

function buildList(items: any, ordered: any): any {
    let h: any = "";
    for (let i: number = 0; i < (items as any[]).length; i++) {
        if (ordered) {
            h = h + (i + 1) + ". " + (items as any[])[i] + "\n";
        } else {
            h = h + "- " + (items as any[])[i] + "\n";
        }
    }
    return h as any;
}
