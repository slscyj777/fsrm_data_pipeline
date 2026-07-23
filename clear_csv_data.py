"""Delete or restore rows for specific stock dates in the monthly CSV backup(s) on SharePoint. Lock and bak files created in same backup_csv folder

Usage:
    uv run utils/clear_csv_data.py --dates 2026-07-21 2026-07-22
    uv run utils/clear_csv_data.py --dates 2026-07-21 --dry-run
    uv run utils/clear_csv_data.py --restore <path-to>/FSRM_consolidated_July_2026.20260721101500.bak
"""
import argparse
import getpass
import json
import logging
import shutil
from collections import defaultdict
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path

import polars as pl

from pipeline.paths import csv_backup_filepath, sp_root, validate_sp_root

logger = logging.getLogger(__name__)

LOCK_SUFFIX = ".lock"
AUDIT_LOG_NAME = "delete_audit.log"
KEEP_BACKUPS_DEFAULT = 3


@contextmanager
def _file_lock(csv_path: Path):
    """Advisory lock so 2 people cant edit the same file."""
    lock_path = csv_path.with_suffix(csv_path.suffix + LOCK_SUFFIX)
    try:
        lock_path.touch(exist_ok=False)
    except FileExistsError as e:
        raise RuntimeError(
            f"{lock_path.name} exists — another process may be writing to {csv_path.name}. "
            "Delete the lock file manually only if you're sure nothing else is running."
        )
    try:
        yield
    finally:
        lock_path.unlink(missing_ok=True)


def _atomic_write(df: pl.DataFrame, csv_path: Path) -> None:
    tmp_path = csv_path.with_suffix(".tmp")
    df.write_csv(tmp_path, float_precision=1)
    tmp_path.replace(csv_path)


def _write_audit_log(csv_path: Path, dates: list[date], removed: int) -> None:
    entry = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "user": getpass.getuser(),
        "file": csv_path.name,
        "dates_removed": [d.isoformat() for d in dates],
        "rows_removed": removed,
    }
    with open(csv_path.parent / AUDIT_LOG_NAME, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def _prune_backups(csv_path: Path, keep: int) -> None:
    backups = sorted(
        csv_path.parent.glob(f"{csv_path.stem}.*.bak"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for stale in backups[keep:]:
        stale.unlink()
        logger.info("Pruned old backup: %s", stale.name)


def delete_stock_dates(
    target_dates: list[date],
    root: Path,
    dry_run: bool = False,
    keep_backups: int = KEEP_BACKUPS_DEFAULT,
) -> None:
    """Removes rows matching target_dates from their respective monthly backup CSVs."""
    by_month: dict[tuple[int, int], list[date]] = defaultdict(list)
    for d in target_dates:
        by_month[(d.year, d.month)].append(d)

    for (year, month), dates in by_month.items():
        csv_path = csv_backup_filepath(date(year, month, 1), root=root)
        if not csv_path.exists():
            logger.warning("No backup file for %d-%02d, skipping: %s", year, month, csv_path)
            continue

        with _file_lock(csv_path):
            df = pl.read_csv(csv_path, schema_overrides={"stock_date": pl.Date}, infer_schema_length=None)
            to_remove = df.filter(pl.col("stock_date").is_in(dates))

            if to_remove.height == 0:
                logger.info("No matching rows for %s in %s", dates, csv_path.name)
                continue

            logger.info("%d rows match %s in %s", to_remove.height, dates, csv_path.name)
            if dry_run:
                continue

            backup_path = csv_path.with_suffix(f".{datetime.now():%Y%m%d%H%M%S}.bak")
            shutil.copy2(csv_path, backup_path)

            remaining = df.filter(~pl.col("stock_date").is_in(dates)).select(df.columns)
            _atomic_write(remaining, csv_path)

            _write_audit_log(csv_path, dates, to_remove.height)
            _prune_backups(csv_path, keep_backups)

            logger.info("Removed %d rows, backup saved to %s", to_remove.height, backup_path.name)
            logger.info("Re-run `uv run main.py --steps excel` to sync %s with this change.", csv_path.name)


def restore_backup(backup_path: Path) -> None:
    """Restores a .bak file created by delete_stock_dates, saving the current state first."""
    if not backup_path.exists():
        raise FileNotFoundError(f"Backup not found: {backup_path}")

    original_name = backup_path.name.rsplit(".", 2)[0] + ".csv"
    csv_path = backup_path.parent / original_name

    with _file_lock(csv_path):
        if csv_path.exists():
            safety_path = csv_path.with_suffix(f".{datetime.now():%Y%m%d%H%M%S}.pre_restore.bak")
            shutil.copy2(csv_path, safety_path)
            logger.info("Current file saved to %s before restoring", safety_path.name)
        shutil.copy2(backup_path, csv_path)
        logger.info("Restored %s from %s", csv_path.name, backup_path.name)


def main():
    parser = argparse.ArgumentParser(description="Delete or restore stock_date rows in the CSV backup(s)")
    parser.add_argument("--dates", nargs="+", help="Dates to remove, YYYY-MM-DD")
    parser.add_argument("--dry-run", action="store_true", help="Preview affected rows, no write")
    parser.add_argument("--yes", action="store_true", help="Skip confirmation prompt")
    parser.add_argument("--keep-backups", type=int, default=KEEP_BACKUPS_DEFAULT, help="Backups to retain per file")
    parser.add_argument("--restore", type=Path, help="Path to a .bak file to restore")
    args = parser.parse_args()

    if args.restore:
        restore_backup(args.restore)
        return

    if not args.dates:
        parser.error("--dates is required unless using --restore")

    target_dates = [datetime.strptime(d, "%Y-%m-%d").date() for d in args.dates]
    root = validate_sp_root(sp_root())

    if not args.dry_run and not args.yes:
        reply = input(f"Delete {len(target_dates)} date(s) from backup CSV(s)? [y/N] ")
        if reply.lower() != "y":
            logger.info("Aborted.")
            return

    delete_stock_dates(target_dates, root=root, dry_run=args.dry_run, keep_backups=args.keep_backups)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    main()