import os

from flask import Flask

DEFAULT_SECRET_KEY = 'dev-insecure-change-me'


def _get_environment_from_env():
    return os.environ.get('HAMPY_ENV', os.environ.get('FLASK_ENV', 'development')).lower()


def _validate_production_secret_key(app):
    if app.config.get('HAMPY_ENV') != 'production':
        return

    secret_key = app.config.get('SECRET_KEY')
    if not secret_key or secret_key == DEFAULT_SECRET_KEY:
        raise RuntimeError(
            'SECRET_KEY must be explicitly configured when HAMPY_ENV=production.'
        )


def create_app(test_config=None):
    #create and configure app
    app = Flask(__name__, instance_relative_config=True)
    environment = _get_environment_from_env()
    app.config.from_mapping(
        SECRET_KEY=DEFAULT_SECRET_KEY,
        DATABASE=os.path.join(app.instance_path, 'contacts.sqlite'),
        HAMPY_ENV=environment,
    )

    if test_config is None:
        #load instance config if there is one when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        #load test config if there is one
        app.config.from_mapping(test_config)

    env_secret_key = os.environ.get('SECRET_KEY')
    if env_secret_key:
        app.config['SECRET_KEY'] = env_secret_key

    _validate_production_secret_key(app)

    #check if instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    #placeholder page that says hello
    @app.route('/hello')
    def hello():
        return "Hello, World!"

#import blueprints
    from . import db
    db.init_app(app)    

    from . import auth
    app.register_blueprint(auth.bp)

    from . import log
    app.register_blueprint(log.bp)
    app.add_url_rule('/', endpoint='index')


    return app    
