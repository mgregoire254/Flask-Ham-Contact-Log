import os

from flask import Flask


def _get_environment():
    return os.environ.get('HAMPY_ENV', os.environ.get('FLASK_ENV', 'development')).lower()


def _get_secret_key(environment):
    configured_secret = os.environ.get('SECRET_KEY')

    if configured_secret:
        return configured_secret

    if environment == 'production':
        raise RuntimeError(
            'SECRET_KEY environment variable is required when HAMPY_ENV=production.'
        )

    return 'dev-insecure-change-me'


def create_app(test_config=None):
    #create and configure app
    app = Flask(__name__, instance_relative_config=True)
    environment = _get_environment()
    app.config.from_mapping(
        SECRET_KEY=_get_secret_key(environment),
        DATABASE=os.path.join(app.instance_path, 'contacts.sqlite'),
        HAMPY_ENV=environment,
    )

    if test_config is None:
        #load instance config if there is one when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        #load test config if there is one
        app.config.from_mapping(test_config)

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
