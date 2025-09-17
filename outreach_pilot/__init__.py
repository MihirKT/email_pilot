from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from .extensions import db, sess, csrf
from config import DevelopmentConfig, ProductionConfig
import os

def create_app(config_class=DevelopmentConfig):
    app = Flask(__name__, instance_relative_config=True)
    if os.environ.get("FLASK_ENV") == "production": config_class = ProductionConfig
    app.config.from_object(config_class)
    try: os.makedirs(app.instance_path)
    except OSError: pass
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    db.init_app(app)
    sess.init_app(app)
    csrf.init_app(app)
    from .auth import routes as auth_blueprint
    app.register_blueprint(auth_blueprint.auth_bp)
    from .campaigns import routes as campaigns_blueprint
    app.register_blueprint(campaigns_blueprint.campaigns_bp)
    from .template_manager import routes as template_manager_blueprint
    app.register_blueprint(template_manager_blueprint.templates_bp, url_prefix='/templates')
    from . import commands
    app.cli.add_command(commands.init_db_command)
    app.cli.add_command(commands.seed_defaults_command)
    return app
