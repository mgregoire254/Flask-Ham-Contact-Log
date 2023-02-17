import os

from flask import Flask

def create_app(test_config=None):
    #create and configure app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        #DONT FORGET TO CHANGE BEFORE PUSHING TO PRODUCTION
        SECRET_KEY='os.environ(secret_key)',
        DATABASE=os.path.join(app.instance_path, 'contacts.sqlite'),
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

