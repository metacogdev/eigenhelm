/**
 * Recursively deep-clones a value, handling plain objects,
 * arrays, Date instances, and RegExp instances.
 */
function deepClone(value) {
    if (value === null || typeof value !== "object") {
        return value;
    }

    if (value instanceof Date) {
        return new Date(value.getTime());
    }

    if (value instanceof RegExp) {
        return new RegExp(value.source, value.flags);
    }

    if (Array.isArray(value)) {
        return value.map(deepClone);
    }

    const cloned = Object.create(Object.getPrototypeOf(value));
    for (const key of Object.keys(value)) {
        cloned[key] = deepClone(value[key]);
    }
    return cloned;
}

module.exports = deepClone;
