#!/usr/bin/env python3
"""Check exact MS lengths and pointers on bundled initialization regressions."""
import argparse
from pathlib import Path
import subprocess
import tempfile


def fasta(path):
    records = {}
    for line in path.read_text().splitlines():
        if line.startswith('>'):
            name = line[1:].split()[0]
            records[name] = ''
        elif line.strip():
            records[name] += line.strip()
    return records


def vectors(path, names):
    rows = []
    for line in path.read_text().splitlines():
        if line.startswith('>'):
            rows.append((line[1:].strip(), []))
        elif line.strip():
            rows[-1][1].extend(map(int, line.split()))
    labels = [name for name, _ in rows]
    if labels not in [names, list(map(str, range(len(names))))]:
        raise ValueError('Unexpected output record identifiers/order')
    return dict(zip(names, (values for _, values in rows)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', type=Path, required=True)
    parser.add_argument('--index', type=Path, required=True, help='raw reference/index prefix')
    parser.add_argument('--case', choices=['toy', 'seed20'], required=True)
    parser.add_argument('--augmented', action='store_true')
    args = parser.parse_args()
    fixture = Path(__file__).resolve().parent / args.case
    reference = (fixture/'reference.txt').read_text()
    if args.index.read_text() != reference:
        parser.error('index prefix must refer to the exact bundled raw reference')
    queries = fasta(fixture/'queries.fa')
    with tempfile.TemporaryDirectory(prefix='phoni-initialization-') as directory:
        reads = Path(directory)/'queries.fa'
        reads.write_text((fixture/'queries.fa').read_text())
        command = [str(args.binary.resolve()), str(args.index.resolve()), '-p', str(reads), '-g', 'naive']
        if args.augmented:
            command += ['-t', 'compressed']
        process = subprocess.run(command, capture_output=True, text=True, timeout=120)
        if process.returncode:
            raise RuntimeError(process.stdout + process.stderr)
        suffix = '.aug' if args.augmented else ''
        lengths = vectors(Path(str(reads)+'.lengths'+suffix), list(queries))
        pointers = vectors(Path(str(reads)+'.pointers'+suffix), list(queries))
        failures = []
        for name, query in queries.items():
            expected = []
            for i in range(len(query)):
                length = 0
                while i+length < len(query) and query[i:i+length+1] in reference:
                    length += 1
                expected.append(length)
            if lengths[name] != expected:
                failures.append(f'{name}: expected {expected}, observed {lengths[name]}')
            elif len(pointers[name]) != len(query):
                failures.append(f'{name}: incorrect pointer count')
            elif any(not (0 <= p <= len(reference)-length) or
                     reference[p:p+length] != query[i:i+length]
                     for i, (p, length) in enumerate(zip(pointers[name], lengths[name]))):
                failures.append(f'{name}: invalid occurrence pointer')
        for failure in failures[:10]:
            print(failure)
        print(f'{len(queries)-len(failures)}/{len(queries)} queries passed ({args.case})')
        return bool(failures)


if __name__ == '__main__':
    raise SystemExit(main())
