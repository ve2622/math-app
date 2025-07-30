from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'tajna_lozinka'
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Kreiranje baze
def init_db():
    with sqlite3.connect('database.db') as con:
        con.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image TEXT,
                question TEXT,
                answer TEXT
            )
        ''')
        con.execute('''
            CREATE TABLE IF NOT EXISTS responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER,
                user_answer TEXT,
                correct INTEGER
            )
        ''')

@app.route('/')
def index():
    return redirect(url_for('student_tasks'))

# Login (fiksni username/password)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == '123':
            session['admin'] = True
            return redirect(url_for('admin_panel'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect('/')

# Admin panel
@app.route('/admin')
def admin_panel():
    if not session.get('admin'):
        return redirect(url_for('login'))
    return render_template('admin.html')

@app.route('/add', methods=['GET', 'POST'])
def add_task():
    if not session.get('admin'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        question = request.form['question']
        answer = request.form['answer']
        image = request.files['image']
        filename = ''
        if image:
            filename = image.filename
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        with sqlite3.connect('database.db') as con:
            con.execute('INSERT INTO tasks (image, question, answer) VALUES (?, ?, ?)',
                        (filename, question, answer))
        return redirect(url_for('admin_panel'))
    return render_template('add_task.html')

# Prikaz zadataka za dete
@app.route('/tasks', methods=['GET', 'POST'])
def student_tasks():
    with sqlite3.connect('database.db') as con:
        tasks = con.execute('SELECT * FROM tasks').fetchall()
    return render_template('student_tasks.html', tasks=tasks)

# Slanje odgovora
@app.route('/submit/<int:task_id>', methods=['POST'])
def submit_answer(task_id):
    user_answer = request.form['answer'].strip()
    with sqlite3.connect('database.db') as con:
        task = con.execute('SELECT * FROM tasks WHERE id = ?', (task_id,)).fetchone()
        already_answered = con.execute('SELECT * FROM responses WHERE task_id = ?', (task_id,)).fetchone()
        if already_answered:
            return "Već si rešio ovaj zadatak. Nema više pokušaja."

        correct = 1 if user_answer == task[3] else 0
        con.execute('INSERT INTO responses (task_id, user_answer, correct) VALUES (?, ?, ?)',
                    (task_id, user_answer, correct))
    return render_template('result.html', correct=correct)

if __name__ == '__main__':
    if not os.path.exists('static/uploads'):
        os.makedirs('static/uploads')
    init_db()
    app.run(debug=True)
