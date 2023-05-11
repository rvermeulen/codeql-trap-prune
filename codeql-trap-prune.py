import argparse
from pathlib import Path
from typing import Dict, List, Any 
import re
import yaml 
from collections import defaultdict
from dataclasses import dataclass

database_metadata = None
def get_database_metadata(database_path: Path) -> Dict[str, Any]:
    global database_metadata
    if database_metadata is None:
        with (database_path / "codeql-database.yml").open() as f:
            database_metadata = yaml.safe_load(f) 
    return database_metadata

def is_unfinished(database_path: Path) -> bool:
    database_metadata = get_database_metadata(database_path)
    return "finalised" in database_metadata and database_metadata["finalised"] == False

def get_primary_language(database_path: Path) -> str:
    database_metadata = get_database_metadata(database_path)
    return database_metadata["primaryLanguage"]

def get_source_trap_mapping(database_path: Path) -> Dict[Path, List[Path]]:
    mapping : Dict[Path, List[Path]] = defaultdict(list)
    source_files_root= database_path / "src"
    trap_files_root = database_path / "trap" / get_primary_language(database_path) / "tarballs"
    for source_file in source_files_root.glob("**/*"):
        if not source_file.is_file():
            continue
        relative_source_file_path = source_file.relative_to(source_files_root)
        for trap_file in (trap_files_root / relative_source_file_path.parent).glob("*"):
            relative_trap_file_path = trap_file.relative_to(trap_files_root)
            if trap_file.is_file() and trap_file.name.startswith(source_file.name):
                mapping[relative_source_file_path].append(relative_trap_file_path)

    return mapping

@dataclass
class ProgramArgs:
    database: Path
    includes: List[re.Pattern[str]]
    excludes: List[re.Pattern[str]]
    dry_run: bool 

def main(args: ProgramArgs) -> int:
    if not args.database.exists():
        print("Database does not exist")
        return 1

    if not is_unfinished(args.database):
        print("Database is not unfinished")
        return 1

    if not args.database.is_absolute():
        args.database = args.database.resolve()

    source_trap_mapping = get_source_trap_mapping(args.database)

    pruned_source_files : set[Path] = set()
    for source_file in source_trap_mapping.keys():
        if any(exclude.fullmatch(str(source_file)) for exclude in args.excludes):
            pruned_source_files.add(source_file)
            continue
        if not any(include.fullmatch(str(source_file)) for include in args.includes):
            pruned_source_files.add(source_file)

    source_root = args.database / "src"
    trap_root = args.database / "trap" / get_primary_language(args.database) / "tarballs"
    for pruned_source_file in pruned_source_files:
        source_file_path = source_root / pruned_source_file
        for pruned_trap_file in source_trap_mapping[pruned_source_file]:
            trap_file_path = trap_root / pruned_trap_file
            if trap_file_path.exists():
                if not args.dry_run:
                    trap_file_path.unlink()
                print(f"Pruned {pruned_trap_file}")
    
        if source_file_path.exists():
            if not args.dry_run:
                source_file_path.unlink()
            print(f"Pruned {pruned_source_file}")
    return 0

if __name__ == '__main__':
    from sys import exit
    parser = argparse.ArgumentParser(description='Trap Prune')
    parser.add_argument('--include', type=re.compile, default=[], dest='includes', action='append', metavar='REGEX', help='Include pattern')
    parser.add_argument('--exclude', type=re.compile, default=[], dest='excludes', action='append', metavar='REGEX', help='Exclude pattern, takes precedence over include')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be pruned without actually pruning TRAP files.')
    parser.add_argument('database', type=Path, help='Unfinished database')
    args = ProgramArgs(**vars(parser.parse_args()))
    if len(args.includes) == 0:
        args.includes.append(re.compile(".*"))
    exit(main(args))