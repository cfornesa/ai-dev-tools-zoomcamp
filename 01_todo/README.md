# 01 Todo

A Django task manager with SQLite persistence, Trash recovery, and recurring
tasks. The original `todo_app` package remains available as a small domain and
CLI compatibility layer; the supported application workflow is the Django web
application.

From the repository root (`ai-dev-tools-zoomcamp`), install the `01_todo`
dependencies once:

```sh
uv --directory 01_todo sync
```

Then open the web interface with one command:

```sh
uv --directory 01_todo run python run_web.py
```

This automatically applies SQLite migrations, starts Django, and opens
`http://127.0.0.1:8000/` in your default browser. Press `Ctrl-C` to stop it.
Use `uv run python run_web.py --no-browser` when launching from an environment
without a desktop browser.

If you are already inside `01_todo`, the equivalent commands are `uv sync` and
`uv run python run_web.py`.

Run the test suite from this directory with:

```sh
python manage.py test
```

Run the command interface with:

```sh
python3 -m todo_app
```

Run it from the `01_todo` directory. With no command it prints help. For
example:

```sh
python3 -m todo_app add "Buy milk"
python3 -m todo_app list
```

Completed tasks remain in storage for history but are hidden from the default
active view. Monthly and yearly recurrence dates clamp to the last valid day of
the target month (for example, January 31 + one month becomes February 28).
