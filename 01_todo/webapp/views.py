from django.contrib import messages
from django.http import Http404, HttpResponseNotAllowed
from django.shortcuts import redirect, render
from todo_app.service import TaskService
from .forms import TaskForm
from .repository import DjangoTaskRepository


def service():
    return TaskService(DjangoTaskRepository())


def active(request):
    return render(request, "webapp/list.html", {"title": "Tasks", "tasks": service().active_tasks()})


def completed(request):
    return render(request, "webapp/list.html", {"title": "Completed", "tasks": service().completed_tasks()})


def trash(request):
    return render(request, "webapp/trash.html", {"tasks": service().trash()})


def create(request):
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            service().create_task(form.cleaned_data["title"], **form.metadata())
            return redirect("active")
    else:
        form = TaskForm()
    return render(request, "webapp/form.html", {"form": form, "title": "New task"})


def edit(request, task_id):
    svc = service()
    try:
        task = svc.repository.get(task_id)
    except KeyError as exc:
        raise Http404 from exc
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            svc.edit_task(task_id, title=form.cleaned_data["title"], **form.metadata())
            return redirect("completed" if task.status.value == "completed" else "active")
    else:
        form = TaskForm(initial={"title": task.title, "notes": task.notes, "tags": ", ".join(task.tags), "due_date": task.due_date,
                                 "priority": task.priority.value if task.priority else "", "recurrence_frequency": task.recurrence.frequency.value if task.recurrence else "",
                                 "recurrence_interval": task.recurrence.interval if task.recurrence else 1})
    return render(request, "webapp/form.html", {"form": form, "title": "Edit task", "task": task})


def _post(request, action, task_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    try:
        action(task_id)
    except (KeyError, ValueError) as exc:
        raise Http404 from exc
    return redirect("active")


def delete(request, task_id): return _post(request, service().move_to_trash, task_id)
def restore(request, task_id): return _post(request, service().restore, task_id)
def complete(request, task_id): return _post(request, service().complete, task_id)
def move(request, task_id, direction): return _post(request, lambda i: service().move(i, int(direction)), task_id)


def empty_trash(request):
    if request.method == "POST" and request.POST.get("confirm") == "yes":
        service().empty_trash(True)
        return redirect("trash")
    if request.method == "POST":
        return redirect("trash")
    return render(request, "webapp/empty_trash.html")
