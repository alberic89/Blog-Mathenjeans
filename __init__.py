import os

from flask import Flask
from flask import render_template
from flask import send_from_directory
from flask_inflate import Inflate
from flask_minify import Minify

from markupsafe import Markup

from jinja2.filters import do_mark_safe

import markdown

md_extensions = [
    "extra",
    "codehilite",
    "abbr",
    "attr_list",
    "def_list",
    "fenced_code",
    "footnotes",
    "tables",
    "admonition",
    "legacy_attrs",
    "legacy_em",
    "meta",
    "nl2br",
    "sane_lists",
    "smarty",
    "toc",
    "wikilinks",
    "markdown_checklist.extension",
    "markdown_del_ins",
    "markdown_mark",
    "markdown_sub_sup",
]

extension_configs = {"codehilite": {"use_pygments": "False"}}


def page_not_found(e):
    return render_template("404.html"), 404


def forbiden(e):
    return render_template("403.html", erreur=e), 403


def create_app(test_config=None):
    """Create and configure an instance of the Flask application."""
    app = Flask(
        __name__,
        instance_relative_config=True,
        static_url_path="",
        static_folder="static",
    )
    app.register_error_handler(404, page_not_found)
    app.register_error_handler(403, forbiden)

    app.config.from_mapping(
        # a default secret that should be overridden by instance config
        SECRET_KEY=os.urandom(40),
        # store the database in the instance folder
        DATABASE=os.path.join(app.instance_path, "flaskr.sqlite"),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # load the test config if passed in
        app.config.update(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    inf = Inflate()
    inf.init_app(app)
    Minify(app=app)

    @app.route("/hello")
    def hello():
        return "Hello, World!"

    @app.route("/favicon.ico")
    def favicon():
        return send_from_directory(
            os.path.join(app.root_path, "static"),
            "favicon.ico",
            mimetype="image/vnd.microsoft.icon",
        )

    @app.route("/robots.txt")
    def robot():
        return send_from_directory(
            os.path.join(app.root_path, "static"),
            "robots.txt",
            mimetype="text/plain",
        )

    # register the database commands
    from flaskr import db

    db.init_app(app)

    # apply the blueprints to the app
    from flaskr import auth, blog

    app.register_blueprint(auth.bp)
    app.register_blueprint(blog.bp)

    # make url_for('index') == url_for('blog.index')
    # in another app, you might define a separate main index here with
    # app.route, while giving the blog blueprint a url_prefix, but for
    # the tutorial the blog will be the main index
    app.add_url_rule("/", endpoint="index")

    @app.template_filter("escape")
    def escape_html(html_text: str) -> Markup:
        return Markup(
            html_text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace("'", "&prime;")
            .replace('"', "&quot;")
        )

    @app.template_filter("markdown")
    def use_markdown(md_text: str) -> Markup:
        return do_mark_safe(
            markdown.markdown(
                md_text,
                extensions=md_extensions,
                extension_configs=extension_configs,
            )
        )

    return app
