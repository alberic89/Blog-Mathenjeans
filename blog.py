from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

from datetime import datetime

bp = Blueprint("blog", __name__)

import locale

locale.setlocale(locale.LC_ALL, 'fr_FR.utf8')

@bp.route("/")
def index():
	"""Show all the posts, most recent first."""
	db = get_db()
	posts = db.execute(
		"SELECT p.id, title, body, created, author_id, username, html, edit, sujet"
		" FROM post p JOIN user u ON p.author_id = u.id WHERE sujet == 0"
		" ORDER BY created DESC"
	).fetchall()
	return render_template("blog/index.html", posts=posts)

@bp.route("/all")
def view_all():
	"""Show all the posts, most recent first."""
	db = get_db()
	posts = db.execute(
		"SELECT p.id, title, body, created, author_id, username, html, edit, sujet"
		" FROM post p JOIN user u ON p.author_id = u.id"
		" ORDER BY created DESC"
	).fetchall()
	return render_template("blog/index.html", posts=posts)

@bp.route("/view/<int:sujet>")
def view(sujet):
	"""Show all the posts, most recent first."""
	db = get_db()
	posts = db.execute(
		"SELECT p.id, title, body, created, author_id, username, html, edit, sujet"
		" FROM post p JOIN user u ON p.author_id = u.id WHERE sujet == ?"
		" ORDER BY created DESC",
			(sujet,),
	).fetchall()
	return render_template("blog/view.html", posts=posts, sujet=sujet)


def get_post(id, check_author=True):
	"""Get a post and its author by id.

	Checks that the id exists and optionally that the current user is
	the author.

	:param id: id of post to get
	:param check_author: require the current user to be the author
	:return: the post with author information
	:raise 404: if a post with the given id doesn't exist
	:raise 403: if the current user isn't the author
	"""
	post = (
		get_db()
		.execute(
			"SELECT p.id, title, body, created, author_id, username, html, sujet"
			" FROM post p JOIN user u ON p.author_id = u.id"
			" WHERE p.id = ?",
			(id,),
		)
		.fetchone()
	)

	if post is None:
		abort(404, f"Le post à l'id {id} n'existe pas.")

	if check_author and post["author_id"] != g.user["id"] and g.user["id"] != 1 :
		abort(403)

	return post


@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
	"""Create a new post for the current user."""
	if request.method == "POST":
		title = request.form["title"]
		body = request.form["body"]
		sujet = request.form["sujet"]
		if g.user["id"] == 1:
			html = bool(request.form["html"])
		else :
			html = False
		
		error = None

		if not title:
			error = "Un titre est requis."
		
		if sujet not in ("0","1","2","3","4") :
			error = "Choisissez un sujet valide !"
		
		if error is not None:
			flash(error)
		else:

			
			db = get_db()
			db.execute(
				"INSERT INTO post (title, body, author_id, html, sujet, created) VALUES (?, ?, ?, ?, ?, ?)",
				(title, body, g.user["id"], html, int(sujet), datetime.now()),
			)
			db.commit()
			if g.user['defsujet']==0 :
				return redirect(url_for("blog.index"))
			else :
				return redirect(url_for("blog.view", sujet=g.user['defsujet']))

	return render_template("blog/create.html")

@bp.route("/<int:id>/")
def show_post(id) :
	db = get_db()
	post = db.execute(
		"SELECT p.id, title, body, created, author_id, username, html, edit, sujet"
		" FROM post p JOIN user u ON p.author_id = u.id WHERE p.id == ?"
		" ORDER BY created DESC",
			(id,),
	).fetchall()
	return render_template("blog/index.html", posts=post)


@bp.route("/<int:id>/update", methods=("GET", "POST"))
@login_required
def update(id):
	"""Update a post if the current user is the author."""
	post = get_post(id)

	if request.method == "POST":
		title = request.form["title"]
		body = request.form["body"]
		sujet = request.form["sujet"]
		if g.user["id"] == 1:
			html = bool(request.form["html"])
		else :
			html = False
		
		error = None

		if not title:
			error = "Un titre est requis."
			
		if sujet not in ("0","1","2","3","4") :
			error = "Choisissez un sujet valide !"
		
		if error is None:
			db = get_db()
			db.execute(
				"UPDATE post SET title = ?, html = ?, edit = ?, sujet = ?, body = ? WHERE id = ?", (title, html, datetime.now(), int(sujet), body, id)
			)
			db.commit()
			
			if g.user['defsujet']==0 :
				return redirect(url_for("blog.index"))
			else :
				return redirect(url_for("blog.view", sujet=g.user['defsujet']))
		else :
			flash(error)

	return render_template("blog/update.html", post=post)


@bp.route("/<int:id>/delete", methods=("POST",))
@login_required
def delete(id):
	"""Delete a post.

	Ensures that the post exists and that the logged in user is the
	author of the post.
	"""
	get_post(id)
	db = get_db()
	db.execute("DELETE FROM post WHERE id = ?", (id,))
	db.commit()
	if g.user['defsujet']==0 :
		return redirect(url_for("blog.index"))
	else :
		return redirect(url_for("blog.view", sujet=g.user['defsujet']))

