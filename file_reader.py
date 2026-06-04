import json
import pathlib

def load_jsonl(filename):
    with open(filename, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue  # skip empty lines
            try:
                record = json.loads(line)
                yield record
            except json.JSONDecodeError as e:
                raise json.JSONDecodeError(f"Error parsing line {line_num}: {e}") from e

def append_to_jsonl(output, filename):
    file_path = pathlib.Path(filename)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.touch(exist_ok=True)
    with open(filename, "a") as f:  # 'a' = append mode
        f.write(json.dumps(output) + "\n")
