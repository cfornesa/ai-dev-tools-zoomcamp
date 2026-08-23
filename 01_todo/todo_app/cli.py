from __future__ import annotations

import argparse
from pathlib import Path

from .model import Priority, RecurrenceFrequency, RecurrenceRule
from .repository import JsonTaskRepository
from .service import TaskService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage tasks")
    parser.add_argument("--store", type=Path, default=Path("tasks.json"))
    sub = parser.add_subparsers(dest="command")
    add = sub.add_parser("add")
    add.add_argument("title")
    add.add_argument("--notes")
    add.add_argument("--tag", action="append", default=[])
    add.add_argument("--due-date")
    add.add_argument("--priority", choices=[p.value for p in Priority])
    add.add_argument("--frequency", choices=[f.value for f in RecurrenceFrequency])
    add.add_argument("--interval", type=int, default=1)
    for name in ("list", "trash", "completed"):
        sub.add_parser(name)
    for name in ("complete", "delete", "restore"):
        command = sub.add_parser(name)
        command.add_argument("id")
    sub.add_parser("empty-trash")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command is None:
        build_parser().print_help()
        return 0
    service = TaskService(JsonTaskRepository(args.store))
    if args.command == "add":
        recurrence = RecurrenceRule(RecurrenceFrequency(args.frequency), args.interval) if args.frequency else None
        if args.frequency and not args.due_date:
            raise SystemExit("--due-date is required with --frequency")
        task = service.create_task(args.title, notes=args.notes, tags=args.tag, due_date=args.due_date,
                                   priority=args.priority, recurrence=recurrence)
        print(task.id)
    elif args.command == "list":
        for task in service.active_tasks():
            print(f"{task.id}  {task.title}")
    elif args.command == "trash":
        for task in service.trash():
            print(f"{task.id}  {task.title}")
    elif args.command == "completed":
        for task in service.completed_tasks():
            print(f"{task.id}  {task.title}")
    elif args.command == "complete":
        completed, next_task = service.complete(args.id)
        print(f"completed {completed.id}")
        if next_task:
            print(f"next {next_task.id} due {next_task.due_date}")
    elif args.command == "delete":
        service.move_to_trash(args.id)
    elif args.command == "restore":
        service.restore(args.id)
    elif args.command == "empty-trash":
        answer = input("Permanently delete all trashed tasks? [y/N] ").strip().lower()
        service.empty_trash(answer == "y")
    return 0
