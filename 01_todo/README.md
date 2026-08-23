# 01 Todo

A dependency-free task manager with an in-memory repository, optional JSON
storage, Trash recovery, and recurring tasks.

Run the test suite from this directory with:

```sh
python3 -m unittest discover -s tests -v
```

Run the command interface with:

```sh
python3 -m todo_app
```

Completed tasks remain in storage for history but are hidden from the default
active view. Monthly and yearly recurrence dates clamp to the last valid day of
the target month (for example, January 31 + one month becomes February 28).
