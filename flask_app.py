import os
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
from collections import defaultdict
from datetime import datetime, timedelta, date
import copy

# Configurações do diretório de upload
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'txt'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Simulação de um banco de dados
tasks = [
    {
        "id": 1,
        "task": "Aprender Flask",
        "category": "Estudos",
        "priority": "Alta",
        "status": "Pendente",
        "due_date": "2025-10-15",
        "recurrence": "Nenhum",
        "subtasks": [
            {"id": 1, "task": "Instalar o Flask", "done": True},
            {"id": 2, "task": "Criar as rotas", "done": False},
        ],
        "attachments": [
            {"type": "link", "name": "Documentação Flask", "url": "https://flask.palletsprojects.com/"},
        ]
    },
    {
        "id": 2,
        "task": "Criar um web app",
        "category": "Trabalho",
        "priority": "Média",
        "status": "Pendente",
        "due_date": "2025-10-20",
        "recurrence": "Nenhum",
        "subtasks": [],
        "attachments": []
    },
    {
        "id": 3,
        "task": "Fazer compras",
        "category": "Pessoal",
        "priority": "Baixa",
        "status": "Concluída",
        "due_date": "2025-10-10",
        "recurrence": "Nenhum",
        "subtasks": [],
        "attachments": []
    }
]

deleted_tasks = []
notes = [
    {"id": 1, "text": "Lembrete: Comprar pão e leite."},
    {"id": 2, "text": "Ideias para o projeto de IA."},
]
deleted_notes = []
categories_data = [
    {"id": 1, "name": "Estudos"},
    {"id": 2, "name": "Trabalho"},
    {"id": 3, "name": "Pessoal"},
]
last_task_id = 3
last_note_id = 2
last_category_id = 3

@app.route("/")
def index():
    global tasks
    
    # Filtros e ordenação
    filtered_tasks = copy.deepcopy(tasks)
    
    category_filter = request.args.get('category', 'Todas as categorias')
    priority_filter = request.args.get('priority', 'Todas as prioridades')
    status_filter = request.args.get('status', 'Todas as tarefas')
    sort_by = request.args.get('sort_by', 'due_date')

    if category_filter != 'Todas as categorias':
        filtered_tasks = [task for task in filtered_tasks if task['category'] == category_filter]
    
    if priority_filter != 'Todas as prioridades':
        filtered_tasks = [task for task in filtered_tasks if task['priority'] == priority_filter]
    
    if status_filter == 'Pendente':
        filtered_tasks = [task for task in filtered_tasks if task['status'] == 'Pendente']
    elif status_filter == 'Concluída':
        filtered_tasks = [task for task in filtered_tasks if task['status'] == 'Concluída']
    
    # Ordenação
    if sort_by == 'priority':
        priority_order = {"Alta": 3, "Média": 2, "Baixa": 1}
        filtered_tasks.sort(key=lambda t: priority_order.get(t.get('priority'), 0), reverse=True)
    elif sort_by == 'due_date':
        filtered_tasks.sort(key=lambda t: t.get('due_date') or '9999-12-31')
    elif sort_by == 'progress':
        filtered_tasks.sort(key=lambda t: t.get('progress', 0), reverse=True)
        
    for task in filtered_tasks:
        if 'subtasks' in task and task['subtasks']:
            done_subtasks = sum(1 for sub in task['subtasks'] if sub['done'])
            task['progress'] = int((done_subtasks / len(task['subtasks'])) * 100)
        else:
            task['progress'] = 0

    # Contagem de tarefas para as estatísticas rápidas
    total_tasks = len(tasks)
    pending_tasks = sum(1 for task in tasks if task['status'] == 'Pendente')
    completed_tasks = sum(1 for task in tasks if task['status'] == 'Concluída')

    # Notificação de tarefas que vencem em breve (próximos 7 dias)
    upcoming_tasks = [task for task in tasks if task.get('due_date') and datetime.strptime(task['due_date'], '%Y-%m-%d').date() <= (datetime.now() + timedelta(days=7)).date() and task['status'] != 'Concluída']
    
    all_categories = sorted(list(set([t['category'] for t in tasks])))
    all_priorities = sorted(list(set([t['priority'] for t in tasks])))
    
    return render_template("index.html",
                           tasks=filtered_tasks,
                           total_tasks=total_tasks,
                           pending_tasks=pending_tasks,
                           completed_tasks=completed_tasks,
                           upcoming_tasks=upcoming_tasks,
                           categories=all_categories,
                           priorities=all_priorities)

@app.route("/add", methods=["POST"])
def add_task():
    global tasks, last_task_id
    new_task_name = request.form.get("task")
    due_date = request.form.get("due_date")
    category = request.form.get("category")
    priority = request.form.get("priority")
    recurrence = request.form.get("recurrence")
    
    if new_task_name:
        last_task_id += 1
        tasks.append({
            "id": last_task_id,
            "task": new_task_name,
            "category": category,
            "priority": priority,
            "status": "Pendente",
            "due_date": due_date,
            "recurrence": recurrence,
            "subtasks": [],
            "attachments": []
        })
    return redirect(url_for("index"))

@app.route("/edit/<int:task_id>", methods=["POST"])
def edit_task(task_id):
    for task in tasks:
        if task["id"] == task_id:
            task["task"] = request.form.get("task")
            task["due_date"] = request.form.get("due_date")
            task["category"] = request.form.get("category")
            task["priority"] = request.form.get("priority")
            task["recurrence"] = request.form.get("recurrence")
            break
    return redirect(url_for("index"))

@app.route("/done/<int:task_id>")
def done_task(task_id):
    for task in tasks:
        if task["id"] == task_id:
            task["status"] = "Concluída" if task["status"] == "Pendente" else "Pendente"
            break
    return redirect(url_for("index"))

@app.route("/delete/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    global tasks, deleted_tasks
    task_to_delete = None
    for task in tasks:
        if task["id"] == task_id:
            task_to_delete = task
            break
    if task_to_delete:
        tasks.remove(task_to_delete)
        deleted_tasks.append(task_to_delete)
    return redirect(url_for("index"))

@app.route("/search")
def search_tasks():
    query = request.args.get('query', '').lower()
    
    if query:
        search_results = [task for task in tasks if query in task['task'].lower()]
    else:
        search_results = tasks

    return render_template("search_results.html", results=search_results, query=query)


@app.route("/add_subtask/<int:task_id>", methods=["POST"])
def add_subtask(task_id):
    subtask_name = request.form.get("subtask")
    for task in tasks:
        if task["id"] == task_id:
            if "subtasks" not in task:
                task["subtasks"] = []
            
            # Gerar ID único para sub-tarefa
            subtask_id = len(task["subtasks"]) + 1
            task["subtasks"].append({"id": subtask_id, "task": subtask_name, "done": False})
            break
    return redirect(url_for("index"))

@app.route("/done_subtask/<int:task_id>/<int:subtask_id>")
def done_subtask(task_id, subtask_id):
    for task in tasks:
        if task["id"] == task_id:
            for subtask in task["subtasks"]:
                if subtask["id"] == subtask_id:
                    subtask["done"] = not subtask["done"]
                    break
            break
    return redirect(url_for("index"))

@app.route("/edit_subtask/<int:task_id>/<int:subtask_id>", methods=["POST"])
def edit_subtask(task_id, subtask_id):
    new_subtask_name = request.form.get("subtask")
    for task in tasks:
        if task["id"] == task_id:
            for subtask in task["subtasks"]:
                if subtask["id"] == subtask_id:
                    subtask["task"] = new_subtask_name
                    break
            break
    return redirect(url_for("index"))

@app.route("/delete_subtask/<int:task_id>/<int:subtask_id>")
def delete_subtask(task_id, subtask_id):
    for task in tasks:
        if task["id"] == task_id:
            task["subtasks"] = [sub for sub in task["subtasks"] if sub["id"] != subtask_id]
            break
    return redirect(url_for("index"))

@app.route("/notes")
def notes_page():
    global notes
    return render_template("notes.html", notes=notes)

@app.route("/add_note", methods=["POST"])
def add_note():
    global notes, last_note_id
    note_text = request.form.get("note")
    if note_text:
        last_note_id += 1
        notes.append({"id": last_note_id, "text": note_text})
    return redirect(url_for("notes_page"))

@app.route("/edit_note/<int:note_id>", methods=["POST"])
def edit_note(note_id):
    global notes
    new_text = request.form.get("note")
    for note in notes:
        if note["id"] == note_id:
            note["text"] = new_text
            break
    return redirect(url_for("notes_page"))

@app.route("/delete_note/<int:note_id>")
def delete_note(note_id):
    global notes, deleted_notes
    note_to_delete = None
    for note in notes:
        if note["id"] == note_id:
            note_to_delete = note
            break
    if note_to_delete:
        notes.remove(note_to_delete)
        deleted_notes.append(note_to_delete)
    return redirect(url_for("notes_page"))
    
@app.route("/categories")
def categories():
    global categories_data, tasks, deleted_tasks
    
    # Agrupar todas as tarefas por categoria
    all_tasks = tasks + deleted_tasks
    grouped_tasks = defaultdict(list)
    for task in all_tasks:
        category_name = task.get("category", "Sem Categoria")
        grouped_tasks[category_name].append(task)
        
    return render_template("categories.html", 
                           categories_data=categories_data,
                           grouped_tasks=grouped_tasks)

@app.route("/add_category", methods=["POST"])
def add_category():
    global categories_data, last_category_id
    category_name = request.form.get("category_name")
    if category_name:
        last_category_id += 1
        categories_data.append({"id": last_category_id, "name": category_name})
    return redirect(url_for("categories"))

@app.route("/edit_category/<int:category_id>", methods=["POST"])
def edit_category(category_id):
    global categories_data, tasks
    new_name = request.form.get("new_category_name")
    for category in categories_data:
        if category["id"] == category_id:
            old_name = category["name"]
            category["name"] = new_name
            
            # Atualizar as tarefas com o novo nome da categoria
            for task in tasks:
                if task["category"] == old_name:
                    task["category"] = new_name
            break
    return redirect(url_for("categories"))

@app.route("/delete_category/<int:category_id>", methods=["POST"])
def delete_category(category_id):
    global categories_data, tasks
    category_to_delete = None
    for category in categories_data:
        if category["id"] == category_id:
            category_to_delete = category
            break
    if category_to_delete:
        for task in tasks:
            if task["category"] == category_to_delete["name"]:
                task["category"] = "Sem Categoria"
        categories_data = [cat for cat in categories_data if cat["id"] != category_id]
    return redirect(url_for("categories"))

@app.route("/recycle_bin")
def recycle_bin():
    global deleted_tasks, deleted_notes
    return render_template("recycle_bin.html", deleted_tasks=deleted_tasks, deleted_notes=deleted_notes)

@app.route("/restore_task/<int:task_id>")
def restore_task(task_id):
    global tasks, deleted_tasks
    task_to_restore = None
    for task in deleted_tasks:
        if task["id"] == task_id:
            task_to_restore = task
            break
    if task_to_restore:
        deleted_tasks.remove(task_to_restore)
        tasks.append(task_to_restore)
    return redirect(url_for("recycle_bin"))

@app.route("/purge_task/<int:task_id>")
def purge_task(task_id):
    global deleted_tasks
    deleted_tasks = [task for task in deleted_tasks if task["id"] != task_id]
    return redirect(url_for("recycle_bin"))
    
@app.route("/restore_note/<int:note_id>")
def restore_note(note_id):
    global notes, deleted_notes
    note_to_restore = None
    for note in deleted_notes:
        if note["id"] == note_id:
            note_to_restore = note
            break
    if note_to_restore:
        deleted_notes.remove(note_to_restore)
        notes.append(note_to_restore)
    return redirect(url_for("recycle_bin"))

@app.route("/purge_note/<int:note_id>", methods=["POST"])
def purge_note(note_id):
    global deleted_notes
    deleted_notes = [note for note in deleted_notes if note["id"] != note_id]
    return redirect(url_for("recycle_bin"))

@app.route('/add_attachment/<int:task_id>', methods=['POST'])
def add_attachment(task_id):
    file = request.files.get('file')
    link_url = request.form.get('link')

    for task in tasks:
        if task['id'] == task_id:
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                task['attachments'].append({
                    'type': 'file',
                    'name': filename,
                    'path': url_for('uploaded_file', filename=filename)
                })
            elif link_url and link_url.strip() != '':
                task['attachments'].append({
                    'type': 'link',
                    'name': link_url,
                    'url': link_url
                })
            break
    return redirect(url_for('index'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/delete_attachment/<int:task_id>/<int:attachment_index>')
def delete_attachment(task_id, attachment_index):
    for task in tasks:
        if task['id'] == task_id:
            if 0 <= attachment_index < len(task['attachments']):
                del task['attachments'][attachment_index]
            break
    return redirect(url_for('index'))

@app.route("/calendar")
def calendar():
    # Ordenar tarefas por data de vencimento
    sorted_tasks = sorted(tasks, key=lambda t: t.get('due_date') or '9999-12-31')
    
    # Agrupar tarefas por data para exibição
    tasks_by_date = defaultdict(list)
    for task in sorted_tasks:
        if task.get('due_date'):
            tasks_by_date[task['due_date']].append(task)
            
    # Obter as datas únicas ordenadas
    sorted_dates = sorted(tasks_by_date.keys())
    
    return render_template("calendar.html", sorted_dates=sorted_dates, tasks_by_date=tasks_by_date)

def update_recurring_tasks():
    global tasks, last_task_id
    today = date.today().isoformat()
    
    for task in tasks:
        if task["status"] == "Concluída" and task.get("recurrence") != "Nenhum":
            task_date = datetime.strptime(task['due_date'], '%Y-%m-%d').date()
            if task_date == date.fromisoformat(today):
                new_task = copy.deepcopy(task)
                last_task_id += 1
                new_task['id'] = last_task_id
                new_task['status'] = "Pendente"
                
                if new_task['recurrence'] == "Diário":
                    new_due_date = task_date + timedelta(days=1)
                elif new_task['recurrence'] == "Semanal":
                    new_due_date = task_date + timedelta(weeks=1)
                elif new_task['recurrence'] == "Mensal":
                    new_due_date = task_date + timedelta(days=30)
                elif new_task['recurrence'] == "Anual":
                    new_due_date = task_date + timedelta(days=365)
                
                new_task['due_date'] = new_due_date.isoformat()
                tasks.append(new_task)

@app.route("/check_recurring")
def check_recurring():
    update_recurring_tasks()
    return redirect(url_for("index"))


if __name__ == "__main__":
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)

