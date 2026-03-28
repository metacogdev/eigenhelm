import json
import os
import sys
import logging


def process_everything(
    data,
    config,
    mode,
    output_path,
    verbose,
    dry_run,
    format_type,
    validate,
    transform,
    filter_fn,
    sort_key,
    reverse,
    limit,
    offset,
    encoding,
    compression,
    checksum,
    retry_count,
    timeout,
    callback,
):
    """Process data through multiple stages. This function does too much."""
    logger = logging.getLogger(__name__)
    results = []
    errors = []
    warnings = []
    stats = {"processed": 0, "skipped": 0, "errors": 0}

    if not data:
        return {"results": [], "errors": ["No data provided"], "stats": stats}

    if validate:
        for i, item in enumerate(data):
            if not isinstance(item, dict):
                errors.append(f"Item {i} is not a dict")
                stats["errors"] += 1
                continue
            if "id" not in item:
                errors.append(f"Item {i} missing id")
                stats["errors"] += 1
                continue
            if "value" not in item:
                warnings.append(f"Item {i} missing value, using default")
                item["value"] = config.get("default_value", 0)

    if filter_fn:
        data = [item for item in data if filter_fn(item)]

    if transform:
        transformed = []
        for item in data:
            try:
                result = transform(item)
                transformed.append(result)
            except Exception as e:
                errors.append(f"Transform failed for {item.get('id', '?')}: {e}")
                stats["errors"] += 1
        data = transformed

    if sort_key:
        try:
            data.sort(key=lambda x: x.get(sort_key, ""), reverse=reverse)
        except Exception as e:
            errors.append(f"Sort failed: {e}")

    if offset:
        data = data[offset:]
    if limit:
        data = data[:limit]

    for item in data:
        try:
            if mode == "json":
                result = json.dumps(item)
            elif mode == "csv":
                result = ",".join(str(v) for v in item.values())
            elif mode == "xml":
                result = (
                    "<item>"
                    + "".join(f"<{k}>{v}</{k}>" for k, v in item.items())
                    + "</item>"
                )
            else:
                result = str(item)

            if compression:
                import zlib

                result = zlib.compress(result.encode(encoding or "utf-8"))

            results.append(result)
            stats["processed"] += 1

            if verbose:
                logger.info(f"Processed: {item.get('id', '?')}")

            if callback:
                callback(item, result)

        except Exception as e:
            errors.append(f"Processing failed for {item.get('id', '?')}: {e}")
            stats["errors"] += 1
            if retry_count and retry_count > 0:
                for attempt in range(retry_count):
                    try:
                        result = str(item)
                        results.append(result)
                        stats["processed"] += 1
                        break
                    except Exception:
                        if attempt == retry_count - 1:
                            stats["skipped"] += 1

    if not dry_run and output_path:
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w", encoding=encoding or "utf-8") as f:
                if format_type == "json":
                    json.dump({"results": results, "stats": stats}, f)
                else:
                    for r in results:
                        f.write(str(r) + "\n")
        except Exception as e:
            errors.append(f"Write failed: {e}")

    return {"results": results, "errors": errors, "warnings": warnings, "stats": stats}
