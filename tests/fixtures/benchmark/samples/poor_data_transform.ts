function transformData(input: any, mappings: any, options: any): any {
  let result: any = {};

  for (let i = 0; i < mappings.length; i++) {
    let mapping = mappings[i];
    let sourceVal: any = input;

    let parts = mapping.source.split(".");
    for (let j = 0; j < parts.length; j++) {
      if (sourceVal != null && sourceVal != undefined) {
        sourceVal = sourceVal[parts[j]];
      }
    }

    if (sourceVal == null || sourceVal == undefined) {
      if (mapping.default != undefined) {
        sourceVal = mapping.default;
      } else {
        continue;
      }
    }

    if (mapping.transform) {
      if (mapping.transform == "uppercase") {
        sourceVal = String(sourceVal).toUpperCase();
      } else if (mapping.transform == "lowercase") {
        sourceVal = String(sourceVal).toLowerCase();
      } else if (mapping.transform == "number") {
        sourceVal = Number(sourceVal);
      } else if (mapping.transform == "boolean") {
        sourceVal = Boolean(sourceVal);
      } else if (mapping.transform == "trim") {
        sourceVal = String(sourceVal).trim();
      } else if (mapping.transform == "split") {
        sourceVal = String(sourceVal).split(mapping.delimiter || ",");
      } else if (mapping.transform == "join") {
        sourceVal = (sourceVal as any).join(mapping.delimiter || ",");
      } else if (mapping.transform == "date") {
        sourceVal = new Date(sourceVal).toISOString();
      }
    }

    let target: any = result;
    let targetParts = mapping.target.split(".");
    for (let k = 0; k < targetParts.length - 1; k++) {
      if (!target[targetParts[k]]) {
        target[targetParts[k]] = {};
      }
      target = target[targetParts[k]];
    }
    target[targetParts[targetParts.length - 1]] = sourceVal;
  }

  if (options && options.postProcess) {
    for (let p = 0; p < options.postProcess.length; p++) {
      let processor = options.postProcess[p];
      if (processor.type == "filter") {
        let keys = Object.keys(result);
        for (let q = 0; q < keys.length; q++) {
          if (processor.exclude && processor.exclude.indexOf(keys[q]) > -1) {
            delete result[keys[q]];
          }
        }
      } else if (processor.type == "merge") {
        let extra: any = processor.data || {};
        let mergeKeys = Object.keys(extra);
        for (let r = 0; r < mergeKeys.length; r++) {
          if (result[mergeKeys[r]] == undefined) {
            result[mergeKeys[r]] = extra[mergeKeys[r]];
          }
        }
      }
    }
  }

  return result;
}
