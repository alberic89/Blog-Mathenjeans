import functools
import uuid

from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash

from flaskr.db import get_db

bp = Blueprint("auth", __name__, url_prefix="/auth")


def send(destemail, subject, message) :
	import smtplib, ssl, os
	smtp_server = 'smtp-mathenjeans.alwaysdata.net'
	port = 465
	destinateur = 'mathenjeans@alwaysdata.net'
	password = os.environ['SMTP_PSWD']
	destinataire = destemail
	message = f'Subject: {subject}\n\n{message}'.encode('utf-8')
	context = ssl.create_default_context()
	try :
		with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
			server.login(destinateur, password)
			server.sendmail(destinateur, destinataire, message)
	except :
		
		raise RuntimeError(f"Impossible d'envoyer l'email à l'adresse {destemail} !")
	
	return True

def login_required(view):
	"""View decorator that redirects anonymous users to the login page."""

	@functools.wraps(view)
	def wrapped_view(**kwargs):
		if g.user is None:
			return redirect(url_for("auth.login"))

		return view(**kwargs)

	return wrapped_view


@bp.before_app_request
def load_logged_in_user():
	"""If a user id is stored in the session, load the user object from
	the database into ``g.user``."""
	user_id = session.get("user_id")

	if user_id is None:
		g.user = None
	else:
		g.user = (
			get_db().execute("SELECT * FROM user WHERE id = ?", (user_id,)).fetchone()
		)


@bp.route("/register", methods=("GET", "POST"))
def register():
	"""Register a new user.

	Validates that the username is not already taken. Hashes the
	password for security.
	"""
	if request.method == "POST":
		username = request.form["username"]
		email = request.form["email"]
		password = request.form["password"]
		confirm = request.form["confirm"]
		sujet = request.form["sujet"]
		db = get_db()
		error = None

		if not username:
			error = "Un nom d'utilisteur est requis."
		elif not password:
			error = "Un mot de passe est requis."
		elif password != confirm :
			error = "Les mots de passe ne correspondent pas !"
		elif not email:
			error = "Une adresse mail est requise."
		elif sujet not in ("0","1","2","3","4") :
			error = "Choisissez un sujet valide !"
		if error is None:
			try:
				db.execute(
					"INSERT INTO user (username, password, email, defsujet) VALUES (?, ?, ?, ?)",
					(username, generate_password_hash(password), email, int(sujet)),
				)
				db.commit()
			except db.IntegrityError:
				# The username was already taken, which caused the
				# commit to fail. Show a validation error.
				error = f"L'utilisateur {username} ou l'adresse {email} est déjà enregistré."
			else:
				# Success, go to the login page.
				return redirect(url_for("auth.login"))

		flash(error)

	return render_template("auth/register.html")


@bp.route("/login", methods=("GET", "POST"))
def login():
	"""Log in a registered user by adding the user id to the session."""
	if request.method == "POST":
		username = request.form["username"]
		password = request.form["password"]
		db = get_db()
		error = None
		user = db.execute(
			"SELECT * FROM user WHERE username = ?", (username,)
		).fetchone()

		if user is None:
			error = "Nom d'utilisateur incorrect."
		elif not check_password_hash(user["password"], password):
			error = "Mot de passe incorrect."

		if error is None:
			# store the user id in a new session and return to the index
			session.clear()
			session["user_id"] = user["id"]
			try :
				if uuid.UUID(password,version=4).version == 4:
					flash('Changez votre mot de passe !!!')
					return redirect(url_for("auth.me"))
			except :
				pass
			if user['defsujet']==0 :
				return redirect(url_for("index"))
			else :
				return redirect(url_for("blog.view", sujet=user['defsujet']))
			

		flash(error)

	return render_template("auth/login.html")

@bp.route("/forget", methods=("GET", "POST"))
def forget():
	if request.method == "POST":
		email = request.form["email"]
		db = get_db()
		error = None
		new_mdp=''
		username=''
		if email is None:
			error = "Veuillez entrer une adresse mail."

		user = db.execute("SELECT username FROM user WHERE email = ?", (email,)).fetchone()
		
		if user == None :
			error = f"Aucun compte ne semble associé à l'adresse {email} !"

		if error is None:
			username = str(user[0])
			new_mdp = str(uuid.uuid4())
			
			try :
				send(email, 'Réinitialisation de votre mot de passe', f'Bonjour,\nVous avez demandé la réinitialisation du mot de passe associé à l\'identifiant {username} sur le blog mathenjeans.\nVotre nouveau mot de passe est : {new_mdp}\nChangez ce mot de passe dès votre prochaine connexion.\nMerci et bonne journée.')
			
			except RuntimeError as e :
				error = e
			
			else :
				db.execute("UPDATE user SET password = ? WHERE username = ?", (generate_password_hash(new_mdp), username))
				db.commit()
				flash(f"Le mot de passe de {username} à bien été réinitialisé. Vérifiez votre boîte mail pour obtenir votre nouveau mot de passe.")
				return redirect(url_for("auth.login"))
			
		
		flash(error)
	
	return render_template("auth/forget.html")

@bp.route("/me", methods=("GET", "POST"))
@login_required
def me():
	if request.method == "POST":
		email=request.form["email"]
		pswd=request.form["password"]
		npswd=request.form["npassword"]
		confirm=request.form["confirm"]
		sujet=request.form["sujet"]
		db = get_db()
		error = None
		mailup = False
		mdpup = False
		sjup = False
		
		if not check_password_hash(g.user["password"], pswd):
				error = 'Mot de passe incorrect.'
		else :
		
			if email != g.user['email']:
				db.execute("UPDATE user SET email = ? WHERE id = ?", (email, g.user['id']))
				mailup = True
			if npswd != '' :
			
				if npswd != confirm :
					error = 'Le mot de passe de confirmation est différent.'
				else :
					db.execute("UPDATE user SET password = ? WHERE id = ?", (generate_password_hash(npswd), g.user['id']))
					mdpup = True
			if sujet != str(g.user['defsujet']) :
				if sujet not in ("0","1","2","3","4") :
					error = "Choisissez un sujet valide !"
				else :
					db.execute("UPDATE user SET defsujet = ? WHERE id = ?", (int(sujet), g.user['id']))
					sjup = True
			
			if mailup or mdpup or sjup :
				db.commit()
			
		if mailup :
			flash(f"L'adresse mail de {g.user['username']} à été mise à jour vers {email}.\n")
		if mdpup :
			flash(f"Le mot de passe de {g.user['username']} à été mis à jour.")
		if sjup :
			flash(f"Le sujet préféré de {g.user['username']} à été mis à jour vers le sujet {sujet}.\n")
		if error is None :
			if sujet=="0" :
				return redirect(url_for("index"))
			else :
				return redirect(url_for("blog.view", sujet=sujet))
		else :
			flash(error)
			
	return render_template("auth/me.html")

@bp.route("/logout")
def logout():
	"""Clear the current session, including the stored user id."""
	session.clear()
	return redirect(url_for("index"))
