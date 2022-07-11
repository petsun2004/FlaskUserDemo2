import uuid, os, hashlib
from flask import Flask, request, render_template, redirect, session, abort, flash
app = Flask(__name__)

# Register the setup page and import create_connection()
from utils import create_connection, setup
app.register_blueprint(setup)

@app.before_request
def restrict():
    restricted_pages = [
        'list_users',
        'view_user',
        'edit_user',
        'delete_user',
        'edit_subject',
        'selected_subject',
        'select_sub'
    ]
    if 'logged_in' not in session and request.endpoint in restricted_pages:
        flash("You must be logged in to view this page.")
        return redirect('/login')

#homePage
@app.route('/')
def home():
    return render_template("index.html")

#register
@app.route('/register', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':

        password = request.form['password']
        encrypted_password = hashlib.sha256(password.encode()).hexdigest()

        with create_connection() as connection:
            with connection.cursor() as cursor:
                sql = """INSERT INTO user_infor
                    (first_name, last_name, email, password)
                    VALUES (%s, %s, %s, %s)
                """
                values = (
                    request.form['first_name'],
                    request.form['last_name'],
                    request.form['email'],
                    encrypted_password,
                )
                cursor.execute(sql, values)
                connection.commit()
        return redirect('/dashboard')
    return render_template('users_add.html')

#login 
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        password = request.form['password']
        encrypted_password = hashlib.sha256(password.encode()).hexdigest()

        with create_connection() as connection:
            with connection.cursor() as cursor:

                # Selects all from user_table where email and password is unique
                sql = "SELECT * FROM user_infor WHERE email=%s AND password=%s"
                values = (
                    request.form['email'],
                    encrypted_password
                )
                cursor.execute(sql, values)
                result = cursor.fetchone()
        if result:
            session['logged_in'] = True
            session['first_name'] = result['first_name']
            session['role'] = result['role']
            session['user_id'] = result['user_id']
            return redirect("/dashboard")
        else:
            flash("Invalid username or password!")

            return redirect("/login")
    else:
        return render_template('login.html')

#logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


#adminOnlyPage
@app.route('/dashboard')
def list_users():
    if session['role'] != 'admin':
        return redirect('/subject')
    with create_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM user_infor")     
            user_result = cursor.fetchall()
            cursor.execute("SELECT * FROM subject_information")     
            subject_result = cursor.fetchall()
    return render_template('users_list.html', user_result=user_result, subject_result=subject_result)

@app.route('/view')
def view_user():
    with create_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM user_infor WHERE user_id=%s", request.args['user_id'])
            result = cursor.fetchone()
    return render_template('users_view.html', result=result)

@app.route('/delete')
def delete_user():
    with create_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM user_infor WHERE user_id=%s", request.args['user_id'])
            connection.commit()
    return redirect('/dashboard')

@app.route('/edit', methods=['GET', 'POST'])
def edit_user():
    # Admin are allowed, users with the right id are allowed, everyone else sees 404.
    if session['role'] != 'admin' and str(session['user_id']) != request.args['user_id']:
        flash("You don't have permission to edit this user.")
        return redirect('/view?user_id=' + request.args['user_id'])

    if request.method == 'POST':
        with create_connection() as connection:
            with connection.cursor() as cursor:
                sql = """UPDATE user_infor SET
                    first_name = %s,
                    last_name = %s,
                    email = %s
                WHERE user_id = %s"""
                values = (
                    request.form['first_name'],
                    request.form['last_name'],
                    request.form['email'],
                    request.form['user_id']
                )
                cursor.execute(sql, values)
                connection.commit()
        return redirect('/view?user_id=' + request.form['user_id'])
    else:
        with create_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM user_infor WHERE user_id = %s", request.args['user_id'])
                result = cursor.fetchone()
        return render_template('users_edit.html', result=result)




#subject table on dashboard 
@app.route('/view_subject')
def view_subject():
    with create_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM subject_information WHERE subject_infor_id=%s", request.args['subject_infor_id'])
            result = cursor.fetchone()
    return render_template('subject_view.html', result=result)

@app.route('/delete_subject')
def delete_subject():
    with create_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM subject_information WHERE subject_infor_id=%s", request.args['subject_infor_id'])
            connection.commit()
    return redirect('/dashboard')

@app.route('/edit_subject', methods=['GET', 'POST'])
def edit_subject():
    # Admin are allowed, users with the right id are allowed, everyone else sees 404.
    if session['role'] != 'admin' and str(session['subject_infor_id']) != request.args['subject_infor_id']:
        flash("You don't have permission to edit this subject.")
        return redirect('/view_subject?subject_infor_id=' + request.args['subject_infor_id'])

    if request.method == 'POST':
        with create_connection() as connection:
            with connection.cursor() as cursor:
                sql = """UPDATE subject_information SET
                    subject_name = %s,
                    describtion = %s,
                    teacher_code = %s,
                    field = %s
                WHERE subject_infor_id = %s"""
                values = (
                    request.form['subject_name'],
                    request.form['describtion'],
                    request.form['teacher_code'],
                    request.form['field'],
                    request.form['subject_infor_id']
                )
                cursor.execute(sql, values)
                connection.commit()
        return redirect('/dashboard?subject_infor_id=' + request.form['subject_infor_id'])
    else:
        with create_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM subject_information WHERE subject_infor_id = %s", request.args['subject_infor_id'])
                result = cursor.fetchone()
        return render_template('subject_edit.html', result=result)


#add new subject 
@app.route('/new_subject', methods=['GET', 'POST'])
def new_subject():
    if request.method == 'POST':
        with create_connection() as connection:
            with connection.cursor() as cursor:
                sql = """INSERT INTO subject_information
                    (subject_name, describtion, teacher_code, field)
                    VALUES (%s, %s, %s, %s)
                """
                values = (
                    request.form['subject_name'],
                    request.form['describtion'],
                    request.form['teacher_code'],
                    request.form['field'],
                )
                cursor.execute(sql, values)
                connection.commit()
        return redirect('/dashboard')
    return render_template('subject_add.html')

#user
# TODO: Add a '/select_subject' route that uses SELECT
@app.route('/select_sub')
def select_sub():
    #add subject into database
    with create_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO student_and_sub (user_id,subject_id) VALUES (%s, %s)", (session['user_id'],request.args['id']))
            connection.commit()
            return redirect('/select_subject')

#subjectPage this page display all the subjects 
@app.route('/subject')
def subject():
    with create_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM subject_information")
            result = cursor.fetchall()
    return render_template('subject_selection.html', result=result, all=True)

#subjectSelection where the end-user can see the subject they chose  
@app.route('/select_subject')
def selected_subject():
    #gets data from database
    with create_connection() as connection:
        with connection.cursor() as cursor:
            if session['role'] != 'admin':
                cursor.execute("SELECT * FROM student_and_sub JOIN user_infor ON user_infor.user_id = student_and_sub.user_id JOIN subject_information ON student_and_sub.subject_id = subject_information.subject_infor_id WHERE user_infor.user_id = %s", session['user_id'])
            else:
                cursor.execute("SELECT * FROM student_and_sub JOIN user_infor ON user_infor.user_id = student_and_sub.user_id JOIN subject_information ON student_and_sub.subject_id = subject_information.subject_infor_id")
            result = cursor.fetchall()
    return render_template('subject_selection.html', result=result, all=False)



if __name__ == '__main__':
    import os

    # This is required to allow sessions.
    app.secret_key = os.urandom(32)

    HOST = os.environ.get('SERVER_HOST', 'localhost')
    try:
        PORT = int(os.environ.get('SERVER_PORT', '5555'))
    except ValueError:
        PORT = 5555
    app.run(HOST, PORT, debug=True)