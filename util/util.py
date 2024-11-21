def format_size(size_bytes) -> str:
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    size = float(size_bytes)
    unit_index = 0

    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1

    return f"{size:.2f} {units[unit_index]}"

def parse_to_integer(value):
    if value[-1] in 'KM':
        multiplier = {'K': 1_000, 'M': 1_000_000}
        return int(float(value[:-1]) * multiplier[value[-1]])
    else:
        return int(value)