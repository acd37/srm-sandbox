from flask import Flask, render_template, url_for, request, session, redirect, jsonify, json, flash
from flask_pymongo import PyMongo
from pymongo import MongoClient
from jinja2 import Template, TemplateNotFound
from flask_dotenv import DotEnv
from bson.json_util import dumps
from bson.objectid import ObjectId
from werkzeug import secure_filename
from flask_mail import Message
from flask_mail import Mail

import pprint
import datetime
import bcrypt
import gridfs

app = Flask(__name__)
env = DotEnv(app)

app.secret_key = 'SECRET_KEY'

app.config['MONGO_URI'] = 'mongodb://heroku_4dkmb0h5:ib9c6pf4aithto894p7tf8db9d@ds251210.mlab.com:51210/heroku_4dkmb0h5'



mail = Mail(app)
mongo = PyMongo(app)

@app.route('/permission_codes')
def permission():
	if 'username' not in session:
		return render_template('index.html')

	classes = mongo.db.classes.find()

	return render_template('permission.html', classes=classes)


@app.route('/register', methods=['GET', 'POST'])
def register():
	if request.method == 'POST':
		users = mongo.db.users
		existing_user = users.find_one({'username' : request.form['username' ]})

		if existing_user is None:
			tokens = mongo.db.tokens
			validation_token = tokens.find_one({ 'token' : request.form['token']})


			if (validation_token):
				hashpass = bcrypt.hashpw(request.form['password'].encode('utf-8'), bcrypt.gensalt())
				users.insert({'tasks': [{"task-body": 'Welcome to your task list. Get started by adding tasks here.', "task-id": "welcome-task"}], 'email' : request.form['email'], 'last_name' : request.form['last_name'], 'first_name' : request.form['first_name'], 'username' : request.form['username'], 'password' : hashpass})
				session['username'] = request.form['username']
				return redirect(url_for('dashboard'))

		flash ('Registration could not be completed. Please try again.')
		return render_template('register.html')

	return render_template('register.html')

@app.route("/")
def index():
	if 'username' in session:

		students = mongo.db.students
		ee_majors = students.find({ "major" : "B.S. Electrical Engineering"}).count()
		ce_majors = students.find({ "major" : "B.S. Computer Engineering"}).count()
		probation_students = students.find({ "standing" : "Probation"}).count()

		users = mongo.db.users
		all_users = mongo.db.users.find()
		current_user = users.find_one({'username' : session["username"]})
		tasks = current_user["tasks"]

		return render_template('dashboard.html',all_users=all_users, users=users, current_user=current_user, tasks=tasks, ce_majors=ce_majors, ee_majors=ee_majors, probation_students=probation_students)


	return render_template('index.html')

@app.route("/dashboard")
def dashboard():
	if 'username' not in session:
		return render_template('index.html')

	students = mongo.db.students
	ee_majors = students.find({ "major" : "B.S. Electrical Engineering"}).count()
	ce_majors = students.find({ "major" : "B.S. Computer Engineering"}).count()
	probation_students = students.find({ "standing" : "Probation"}).count()

	users = mongo.db.users
	all_users = mongo.db.users.find()
	print(all_users)
	current_user = users.find_one({'username' : session["username"]})
	tasks = current_user["tasks"]

	return render_template('dashboard.html',all_users=all_users, current_user=current_user, tasks=tasks, ce_majors=ce_majors, ee_majors=ee_majors, probation_students=probation_students)

@app.route('/login', methods=['POST'])
def login():
	users = mongo.db.users
	login_user = users.find_one({'username' : request.form['username']})

	if login_user:
		if bcrypt.hashpw(request.form['password'].encode('utf-8'), login_user['password'].encode('utf-8')) == login_user['password'].encode('utf-8'):
			session['username'] = request.form['username']
			return redirect(url_for('dashboard'))
		return 'Invalid username/password combination'
	return 'Invalid username/password combination'

@app.route("/student/<string:student_oid>")
def student(student_oid):
	if 'username' not in session:
		return render_template('index.html')

	students = mongo.db.students
	current_student = students.find_one({'_id' : ObjectId(student_oid)})
	return render_template('student.html', current_student=current_student)

@app.route('/update_major', methods=['GET', 'POST'])
def update_major():
	if 'username' not in session:
		return render_template('index.html')

	if request.method == 'POST':
		students = mongo.db.students
		new_major = request.form['update-major']
		student_oid = request.form['student_major_id']
		current_student = students.find_one({'_id' : ObjectId(student_oid)})
		now = datetime.datetime.now()
		time_stamp_id = now.strftime("%Y%m%d%H%M")
		time_stamp = now.strftime("%Y-%m-%d %H:%M")
		note_id = time_stamp_id + '_?' + student_oid

		students.update(
			{ "_id": ObjectId(student_oid) },
			{ "$set":
				{
					"major": new_major
				}
			}
		)

		students.update(
			{ "_id": ObjectId(student_oid) },
			 {"$push": {
				"notes": {
					"$each": [{
						"note_body": "Major updated to: " + new_major,
						"note_time": time_stamp,
						"note_id": note_id
					}],
					"$position": 0
				}
			 	}
				}
			)


		flash('Student saved.')
		return redirect(request.referrer)
	return render_template('student.html', current_student=current_student)

@app.route('/update_standing', methods=['GET', 'POST'])
def update_standing():
	if 'username' not in session:
		return render_template('index.html')

	if request.method == 'POST':
		students = mongo.db.students

		new_standing = request.form['update-standing']
		student_oid = request.form['student_major_id']
		current_student = students.find_one({'_id' : ObjectId(student_oid)})

		date = request.form['probation_date']
		cum_gpa = request.form['cum_gpa']
		tech_gpa = request.form['tech_gpa']

		now = datetime.datetime.now()
		time_stamp = now.strftime("%Y-%m-%d %H:%M")
		time_stamp_id = now.strftime("%Y%m%d%H%M")
		note_id = time_stamp_id + '_?' + student_oid

		students.update(
			{ "_id": ObjectId(student_oid) },
			{ "$set":
				{
					"standing": new_standing
				}
			}
		)

		students.update(
			{ "_id": ObjectId(student_oid) },
		 {"$push": {
			"notes": {
				"$each": [{
					"note_body": "Standing Change Date: " + date + " | Cumulative GPA: " + cum_gpa + " | Technical GPA: " + tech_gpa + " | Status: " + new_standing,
					"note_time": time_stamp,
					"note_id": note_id
				}],
				"$position": 0
			}
		 	}
			}
		)


		flash('Student saved.')
		return redirect(request.referrer)
	return render_template('student.html', time_stamp = time_stamp, current_student=current_student)

@app.route('/update_transfer', methods=['GET', 'POST'])
def update_transfer():
	if 'username' not in session:
		return render_template('index.html')

	if request.method == 'POST':
		students = mongo.db.students
		current_oid = request.form['student_major_id']
		current_student = students.find_one({'_id' : ObjectId(current_oid) })
		new_transfer = request.form['update-transfer']

		students.update(
			{ "_id": ObjectId(current_oid) },
			{ "$set":
				{
					"transfer": new_transfer
				}
			}
		)
		flash('Student saved.')
		return redirect(request.referrer)
	return render_template('student.html', current_student=current_student)


@app.route('/update_phone', methods=['GET', 'POST'])
def update_phone():
	if 'username' not in session:
		return render_template('index.html')

	if request.method == 'POST':
		students = mongo.db.students
		current_oid = request.form['student_major_id']
		current_student = students.find_one({'student_id' : ObjectId(current_oid) })
		new_phone= request.form['update-phone']

		students.update(
			{ "_id": ObjectId(current_oid) },
			{ "$set":
				{
					"phone": new_phone
				}
			}
		)
		flash('Student saved.')
		return redirect(request.referrer)
	return render_template('student.html', current_student=current_student)



@app.route('/update_email', methods=['GET', 'POST'])
def update_email():
	if 'username' not in session:
		return render_template('index.html')

	if request.method == 'POST':
		students = mongo.db.students
		current_oid = request.form['student_major_id']
		current_student = students.find_one({'_id' : ObjectId(current_oid)})
		new_email= request.form['update-email']

		students.update(
			{ "_id": ObjectId(current_oid) },
			{ "$set":
				{
					"email": new_email
				}
			}
		)
		flash('Student saved.')
		return redirect(request.referrer)
	return render_template('student.html', current_student=current_student)

@app.route('/update_uid', methods=['GET', 'POST'])
def update_uid():
	if 'username' not in session:
		return render_template('index.html')

	if request.method == 'POST':
		students = mongo.db.students
		current_oid = request.form['student_major_id']
		current_student = students.find_one({'_id' : ObjectId(current_oid)})
		new_uid = request.form['update-uid']

		students.update(
			{ "_id": ObjectId(current_oid) },
			{ "$set":
				{
					"student_id": new_uid
				}
			}
		)
		flash('Student saved.')
		return redirect(request.referrer)
	return render_template('student.html', current_student=current_student)

@app.route('/update_direct', methods=['GET', 'POST'])
def update_direct():
	if 'username' not in session:
		return render_template('index.html')

	if request.method == 'POST':
		students = mongo.db.students
		current_oid = request.form['student_direct_admit']
		current_student = students.find_one({'_id' : ObjectId(current_oid)})
		new_admit_status = request.form['update-direct']

		students.update(
			{ "_id": ObjectId(current_oid) },
			{ "$set":
				{
					"direct_admit": new_admit_status
				}
			}
		)
		flash('Student saved.')
		return redirect(request.referrer)
	return render_template('student.html', current_student=current_student)

@app.route('/exceptions', methods=['GET', 'POST'])
def exceptions():
	if 'username' not in session:
		return render_template('index.html')

	if request.method == 'POST':
		students = mongo.db.students
		now = datetime.datetime.now()
		time_stamp = now.strftime("%Y-%m-%d %H:%M")
		current_student = students.find_one({'student_id' : request.form['student-exception-id']})
		current_id = request.form['student-exception-id']

		exception = request.form['student-exception']

		students.update(
   			{ "student_id": current_id },
   			{ "$push": {
				"exceptions": {
					"$each": [{
						"exception_body": exception,
						"exception_time": time_stamp
					}],
					"$position": 0
				}
			}
			}
		)

		flash('Student saved.')
		return redirect(request.referrer)
	return render_template('student.html', current_student=current_student)


@app.route('/delete_todo/<string:todo_id>')
def delete_todo(todo_id):
	if 'username' not in session:
		return render_template('index.html')

	users = mongo.db.users
	current_user = users.find_one({'username' : session["username"]})
	current_task_id = todo_id

	print(current_task_id)

	users.update({ "username": session["username"]},
					{ '$pull' :
						{ 'tasks':
						 { 'task-id': todo_id } } }
				)
	return redirect(request.referrer)


@app.route('/delete_student', methods=['GET', 'POST'])
def delete_student():
	if 'username' not in session:
		return render_template('index.html')

	students = mongo.db.students
	current_id = request.form['student_delete']
	print(current_id)

	student = students.find_one( { '_id' : ObjectId(current_id) } )
	students.delete_one(student)
	flash('Student successfully deleted.')
	return redirect('/dashboard')


@app.route('/delete_note/<string:note_id>')
def delete_note(note_id):
	if 'username' not in session:
		return render_template('index.html')

	students = mongo.db.students
	print(note_id)

	current_note = mongo.db.students.find_one({
		"notes": {
			"$elemMatch": {
				"note_id": note_id
			}
		}
	}, {
		"notes.$.note_id": 1
	})

	print(current_note)
	student_id = current_note['_id']

	students.update({ "_id": ObjectId(student_id) },
					{'$pull':
						{ "notes":
							{ 'note_id': note_id } } }
					)

	return redirect(request.referrer)


@app.route('/add_followup', methods=['GET', 'POST'])
def add_followup():
	if 'username' not in session:
		return render_tempalte('index.html')

	if request.method == 'POST':

		students = mongo.db.students
		users = mongo.db.users

		current_student = students.find_one({'student_id' : request.form['student-followup-id']})
		current_student_id = request.form['student-followup-id']
		name = current_student['first_name'] + " " + current_student['last_name']
		reminder_body = request.form['student-followup-body']
		now = datetime.datetime.now()
		followup_id =  now.strftime("%Y%m%d%H%M")
		followup_body = "Follow-up Task: " + name + " (" + current_student_id + "). " + reminder_body

		users.update(
			{"username": session['username']},
			{"$push": {
				"tasks": {
					"$each": [{
						"task-body": followup_body,
						"task-id": followup_id
					}],
					"$position" : 0
				}
			}}
		)

	return redirect(request.referrer)

@app.route('/add_todo', methods=['GET', 'POST'])
def add_todo():
	if 'username' not in session:
		return render_template('index.html')

	if request.method == 'POST':
		users = mongo.db.users
		now = datetime.datetime.now()
		time_stamp = now.strftime("%Y-%m-%d %H:%M")
		task_id = now.strftime("%Y%m%d%H%M")
		current_user = users.find_one({'username' : session["username"]})
		todo_item = request.form['user-todo']
		print(current_user["username"])


		users.update(
			{"username": request.form['assigned-user']},
			{"$push": {
				"tasks": {
					"$each": [{
						"task-body": todo_item,
						"task-id": task_id
					}],
					"$position" : 0
				}
			}}
		)

		assigned = users.find_one({ 'username' : request.form['assigned-user']})
		assigned_username = assigned['username']
		assigned_email = assigned['email']
		print(assigned_email)

		if current_user['username'] != assigned_username:

			msg = Message("Task Assignment", sender="ecegrad@ece.utah.edu", recipients=[assigned_email])
			msg.html = render_template('task.html', assigned=assigned, current_user=current_user, todo_item=todo_item)
			mail.send(msg)
			print(msg)

		return redirect(request.referrer)
	return render_template('dashboard.html')


@app.route('/add_note', methods=['GET', 'POST'])
def add_note():
	if 'username' not in session:
		return render_template('index.html')

	if request.method == 'POST':
		students = mongo.db.students
		now = datetime.datetime.now()
		time_stamp = now.strftime("%Y-%m-%d %H:%M")
		time_stamp_id = now.strftime("%Y%m%d%H%M")
		current_student = students.find_one({'student_id' : request.form['student-note-id']})
		current_id = request.form['student-note-id']
		note = request.form['student-note']
		note_id = time_stamp_id

		students.update(
   			{ "student_id": current_id },
   			{ "$push": {
				"notes": {
					"$each": [{
						"note_body": note,
						"note_time": time_stamp,
						"note_id": note_id
					}],
					"$position": 0
				}
			}
			}
		)

		flash('Student saved.')
		return redirect(request.referrer)
	return render_template('student.html', current_student=current_student)

@app.route("/find_all")
def find_all():
	if 'username' not in session:
		return render_template('index.html')

	students = mongo.db.students.find()
	return render_template('view-students.html', students=students)

@app.route("/find_ee")
def find_ee():
	if 'username' not in session:
		return render_template('index.html')

	students = mongo.db.students.find({"major" : "B.S. Electrical Engineering" })
	return render_template('view-students.html', students=students)

@app.route("/find_transfer")
def find_transfer():
	if 'username' not in session:
		return render_template('index.html')

	students = mongo.db.students.find({"transfer" : "yes" })
	return render_template('view-students.html', students=students)

@app.route("/find_prospective")
def find_prospective():
	if 'username' not in session:
		return render_template('index.html')

	students = mongo.db.students.find({"major" : "Prospective Student" })
	return render_template('view-students.html', students=students)

@app.route("/find_direct")
def find_direct():
	if 'username' not in session:
		return render_template('index.html')

	students = mongo.db.students.find({"direct_admit" : "yes" })
	return render_template('view-students.html', students=students)


@app.route("/find_ce")
def find_ce():
	if 'username' not in session:
		return render_template('index.html')

	students = mongo.db.students.find({"major" : "B.S. Computer Engineering" })
	return render_template('view-students.html', students=students)

@app.route("/probation")
def probation():
	if 'username' not in session:
		return render_template('index.html')

	students = mongo.db.students.find({"standing" : "Probation" })
	return render_template('view-students.html', students=students)



@app.route("/find_name", methods=['GET', 'POST'])
def find_name():
	if 'username' not in session:
		return render_template('index.html')

	if request.method == 'POST':
		result = request.form['name-input']

		first_char = list(result)
		print(first_char)
		if first_char[0] == "0":
			first_char[0] = 'u'
			result = ''.join(first_char)


		students = mongo.db.students.find(
		{ "$or" : [
			{"last_name" : result},
			{"student_id" : result},
			{"first_name" : result},
			{"phone" : result},
			{"standing" : result}
		]}).collation( { "locale": "en_US", "strength": 1, "alternate": "shifted"  })
	return render_template('view-students.html', students=students)


@app.route("/view-students")
def view_students():
	if 'username' not in session:
		return render_template('index.html')

	return render_template('view-students.html')

@app.route("/add-student")
def add_student():
	if 'username' not in session:
		return render_template('index.html')


	return render_template('add-student.html')


@app.route('/add', methods=['GET','POST'])
def add():
	if request.method == 'POST':
		students = mongo.db.students
		existing_student = students.find_one({'student_id' : request.form['student_id']})

		if existing_student is None:
			students.insert({'first_name' : request.form['first_name'],
				'last_name' : request.form['last_name'],
				'student_id' : request.form['student_id'],
				'major' : request.form['major'],
				'standing' : request.form['standing'],
				'email' : request.form['email'],
				'phone' : request.form['phone'],
				'direct_admit' : request.form['direct'],
				'transfer' : request.form['transfer']})
			flash("Student successfully added!")
			return redirect(url_for('add'))

		flash("A student with that ID already exists!")


	return render_template('add-student.html')

@app.route('/finalize', methods=['GET','POST'])
def finalize():
	if request.method =='POST':
		students = mongo.db.students
		student_oid = request.form['student_finalize']

		students.update(
			{ "_id": ObjectId(student_oid) },
			{ "$set":
				{
					"enrollment_date": request.form['enrollment_date'],
					"graduation_date": request.form['graduation_date'],
					"graduation_gpa": request.form['student_cum_gpa']
				}
			}
		)
		return redirect(request.referrer)
		return render_template('student.html')

@app.route('/logout')
def logout():
	session.clear()
	return redirect(url_for('index'))


if __name__ == "__main__":
	app.run(debug=True)
