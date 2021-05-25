# importing the modules
from flask import Flask, render_template, request, redirect, session, url_for
from flask_mysqldb import MySQL
import MySQLdb.cursors

import smtplib

# app config
app = Flask(__name__)
app.config['MYSQL_HOST'] = 'remotemysql.com'
app.config['MYSQL_USER'] = 'aiHAmgX98Q'
app.config['MYSQL_PASSWORD'] = 'Up6JQHTJDj'
app.config['MYSQL_DB'] = 'aiHAmgX98Q'
mysql = MySQL(app)
app.secret_key = 'blacksheep'


# routes

# home
@app.route("/",methods=['GET',"POST"])
def home():
	if ('user' not in session.keys()) or (session['user'] == None):
		return redirect("https://akshayapp.apps.pcfdev.in/login")
	else:
		cursor = mysql.connection.cursor()
		cursor.execute("SELECT * FROM User WHERE id = % s",[session['user']])
		userdetails = cursor.fetchone()
		if userdetails[3] == 2:
			return render_template("home.html",user=userdetails)
		elif userdetails[3] == 1:
			cursor.execute("SELECT * FROM Tickets WHERE agent=%s",[session['user']])
			tickets = cursor.fetchall()
			return render_template("home.html",user=userdetails,tickets=tickets)
		else:
			if request.method == "POST":
				title = request.form['title']
				description = request.form['description']
				cust_id = session['user']
				cursor = mysql.connection.cursor()
				cursor.execute("INSERT INTO Tickets(customer,title,description) VALUES(%s,%s,%s)",(cust_id,title,description))
				mysql.connection.commit()
				cursor.execute("SELECT * FROM User WHERE id = % s",[session['user']])
				userdetails = cursor.fetchone()
				cursor.execute("SELECT * FROM Tickets WHERE customer = %s",[session['user']])
				tickets = cursor.fetchall()
				return render_template("home.html",msg="Ticket Filed",user=userdetails,tickets=tickets)
			cursor = mysql.connection.cursor()
			cursor.execute("SELECT * FROM User WHERE id = % s",[session['user']])
			userdetails = cursor.fetchone()
			cursor.execute("SELECT * FROM Tickets WHERE customer = %s",[session['user']])
			tickets = cursor.fetchall()
			return render_template("home.html",user=userdetails,tickets=tickets)

# user account registration
@app.route("/register",methods=["GET","POST"])
def register_account():
	if request.method == "POST":
		username = request.form['username']
		email = request.form['email']
		phonenumber = request.form['phonenumber']
		password = request.form['password']
		cursor = mysql.connection.cursor()
		cursor.execute("INSERT INTO User(username,email,phonenumber,password,role) VALUES(%s,%s,%s,%s,%s)",(username,email,phonenumber,password,0))
		mysql.connection.commit()
		return redirect("https://akshayapp.apps.pcfdev.in/login")
	return render_template("register.html")

# login
@app.route('/login',methods=["GET","POST"])
def login():
	if request.method == "POST":
		email = request.form['email']
		password = request.form['password']
		cursor = mysql.connection.cursor()
		cursor.execute("SELECT * FROM User WHERE email = % s",[email])
		userdetails = cursor.fetchone()
		if userdetails:
			if (password == userdetails[2]):
				session['user'] = userdetails[4]
				return redirect("https://akshayapp.apps.pcfdev.in/")
			else:
				msg = "Incorrect Password"
		else:
			msg = "User does not exist"
		return render_template("login.html",msg=msg)
	return render_template("login.html")

# logout

@app.route("/logout")
def logout():
	session['user'] = None
	return redirect("https://akshayapp.apps.pcfdev.in/")


# ticket detail
@app.route("/ticket/<int:id>",methods=["GET","POST"])
def ticket_detail(id):
	cursor = mysql.connection.cursor()
	cursor.execute("SELECT * FROM Tickets WHERE id=%s",[id])
	ticket = cursor.fetchone()
	cursor.execute("SELECT * FROM User WHERE id=%s",[session['user']])
	user = cursor.fetchone()
	cursor.execute("SELECT * FROM User WHERE role=1")
	all_users = cursor.fetchall()
	if user is None:
		return redirect("https://akshayapp.apps.pcfdev.in/login")
	if request.method == "POST":
		agent = request.form['agent']
		print(agent,id)
		cursor.execute("UPDATE Tickets SET agent= %s WHERE id = %s",(agent,id))
		cursor.execute("UPDATE Tickets SET progress='assigned' WHERE id = %s",[id])
		mysql.connection.commit()

		cursor.execute("SELECT email FROM User WHERE id=(SELECT customer FROM Tickets WHERE id= % s)",[id])
		email = cursor.fetchall()
		TEXT = "Hello Customer,\n An Agent is successfully assigned to you.The Agent will contact you soon.\n To keep a track of your ticket, please visit our website dashboard."
		SUBJECT = "Agent Assigned"
		message = 'Subject: {}\n\n{}'.format(SUBJECT, TEXT)
		server = smtplib.SMTP("smtp.gmail.com",587)
		server.starttls()
		server.login("vmwarecustomecare@gmail.com","vmware123")
		server.sendmail("vmwarecustomecare@gmail.com", email, message)

		return redirect("https://akshayapp.apps.pcfdev.in/panel")
	return render_template("details.html",ticket=ticket,user=user,all_users=all_users)


# admin register
@app.route("/admin/register",methods=["GET","POST"])
def admin_register():
	if request.method == "POST":
		username = request.form['username']
		email = request.form['email']
		phonenumber = request.form['phonenumber']
		password = request.form['password']
		secret_key = request.form['secret']
		if secret_key == "12345":
			cursor = mysql.connection.cursor()
			cursor.execute("INSERT INTO User(username,email,phonenumber,password,role) VALUES(%s,%s,%s,%s,%s)",(username,email,phonenumber,password,2))
			mysql.connection.commit()
			return redirect("https://akshayapp.apps.pcfdev.in/login")
		else:
			return render_template("admin_register.html",msg="Invlaid Secret")

	return render_template("admin_register.html")

# promote agent
@app.route("/panel",methods=['GET','POST'])
def panel():
	id = session['user']
	if id is None:
		return redirect("https://akshayapp.apps.pcfdev.in/login")
	cursor = mysql.connection.cursor()
	cursor.execute("SELECT * FROM User WHERE id=%s",[id])
	user_details = cursor.fetchone()
	if user_details[3] != 2:
		return "You do not have administrator privileges"
	else:
		cursor.execute("SELECT * FROM User WHERE role=0")
		all_users = cursor.fetchall()
		cursor.execute("SELECT * FROM Tickets WHERE progress IS NULL")
		tickets = cursor.fetchall()
		if request.method == "POST":
			user_id = request.form['admin-candidate']
			cursor = mysql.connection.cursor()
			cursor.execute("UPDATE User SET role=1 WHERE id = %s",(user_id,))
			mysql.connection.commit()
			return redirect("https://akshayapp.apps.pcfdev.in/panel")
		return render_template("panel.html",all_users=all_users,user=user_details,tickets=tickets)


@app.route("/accept/<int:ticket_id>/<int:user_id>")
def accept(ticket_id,user_id):
	cursor = mysql.connection.cursor()
	cursor.execute("SELECT * FROM User WHERE id = %s",[user_id])
	agent = cursor.fetchone()
	cursor.execute("SELECT * FROM Tickets WHERE id=%s",[ticket_id])
	ticket = cursor.fetchone()
	if agent[4] == ticket[2]:
		cursor.execute("UPDATE Tickets SET progress='accepted' WHERE id=%s",[ticket_id])
		mysql.connection.commit()
	return redirect("https://akshayapp.apps.pcfdev.in/")

@app.route("/delete/<int:ticket_id>/<int:user_id>")
def delete(ticket_id,user_id):
	cursor = mysql.connection.cursor()
	cursor.execute("SELECT * FROM User WHERE id = %s",[user_id])
	agent = cursor.fetchone()
	cursor.execute("SELECT * FROM Tickets WHERE id=%s",[ticket_id])
	ticket = cursor.fetchone()
	if agent[4] == ticket[2]:
		cursor.execute("DELETE FROM Tickets WHERE id=%s",[ticket_id])
		mysql.connection.commit()
	return redirect("https://akshayapp.apps.pcfdev.in/")


# run server
if __name__ == "__main__":
	app.run( host ='0.0.0.0',debug=True,port =8080)
