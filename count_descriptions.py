from pathlib import Path
import argparse
import json
import re
from collections import Counter, defaultdict

level_pattern = re.compile(r"Complexity:\s*(L\d+)\b")


def extract_prefix(filename: str) -> str:
    stem = Path(filename).stem
    return re.sub(r"_\d+$", "", stem)


def level_sort_key(level_name: str):
    m = re.match(r"L(\d+)$", level_name)
    if m:
        return (0, int(m.group(1)))
    return (1, level_name)


parser = argparse.ArgumentParser(
    description="Cuenta descriptions de tasks JSON y muestra ejemplos de archivos."
)
parser.add_argument(
    "--base-path",
    default="data/dev",
    help="Directorio que contiene los archivos JSON a procesar.",
)
parser.add_argument(
    "--examples-per-description",
    type=int,
    default=0,
    help="Cantidad de nombres de archivo a mostrar por cada description.",
)
args = parser.parse_args()

base_path = Path(args.base_path)
examples_per_description = max(0, args.examples_per_description)


# Vista 1: level -> description -> Counter(prefix)
by_level = defaultdict(lambda: defaultdict(Counter))

# Vista 2: prefix -> Counter(description)
by_prefix = defaultdict(Counter)

# Ejemplos: description -> [filenames]
files_by_description = defaultdict(list)

total_by_level = Counter()
total_by_prefix = Counter()
grand_total = 0

for json_file in base_path.glob("*.json"):
    try:
        with json_file.open("r", encoding="utf-8") as f:
            data = json.load(f)

        description = data.get("target_schema", {}).get("description")
        if not description:
            continue

        match = level_pattern.search(description)
        level = match.group(1) if match else "UNKNOWN"
        prefix = extract_prefix(json_file.name)

        by_level[level][description][prefix] += 1
        by_prefix[prefix][description] += 1
        files_by_description[description].append(json_file.name)

        total_by_level[level] += 1
        total_by_prefix[prefix] += 1
        grand_total += 1

    except Exception as e:
        print(f"Error procesando {json_file}: {e}")


print("=== AGRUPADO POR NIVEL -> DESCRIPTION -> PREFIJO ===\n")

for level in sorted(by_level.keys(), key=level_sort_key):
    print(f"{level} - total: {total_by_level[level]}")

    descriptions = by_level[level]
    description_totals = {
        description: sum(prefix_counter.values())
        for description, prefix_counter in descriptions.items()
    }

    for description, desc_total in sorted(
        description_totals.items(),
        key=lambda x: (-x[1], x[0])
    ):
        one_line = description.replace("\n", " ")
        print(f"  {desc_total:>3}  {one_line}")

        if examples_per_description:
            examples = sorted(files_by_description[description])[:examples_per_description]
            if examples:
                print(f"       examples: {', '.join(examples)}")

        prefix_counter = descriptions[description]
        for prefix, prefix_count in sorted(
            prefix_counter.items(),
            key=lambda x: (-x[1], x[0])
        ):
            print(f"       {prefix}: {prefix_count}")

    print()

print("=== AGRUPADO POR PREFIJO -> DESCRIPTION ===\n")

for prefix in sorted(
    by_prefix.keys(),
    key=lambda p: (-total_by_prefix[p], p)
):
    print(f"{prefix} - total: {total_by_prefix[prefix]}")

    for description, count in sorted(
        by_prefix[prefix].items(),
        key=lambda x: (-x[1], x[0])
    ):
        one_line = description.replace("\n", " ")
        print(f"  {count:>3}  {one_line}")

        if examples_per_description:
            examples = sorted(files_by_description[description])[:examples_per_description]
            if examples:
                print(f"       examples: {', '.join(examples)}")

    print()

print(f"TOTAL GENERAL: {grand_total}")
