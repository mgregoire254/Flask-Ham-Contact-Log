from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from Contacts.auth import login_required
from Contacts.db import get_db

bp = Blueprint('log', __name__)

#index view
@bp.route('/')
@login_required
def index():
    db = get_db()
    contacts = db.execute(
        'SELECT p.id, callsign, comments, created, author_id, username, frequency, mode, power, self_location, contact_location, self_rst, contact_rst'
        ' FROM contacts p JOIN user u ON p.author_id = u.id'
        ' ORDER BY created DESC'
    ).fetchall()
    return render_template('log/index.html', contacts=contacts)

# create view
@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        callsign = request.form['callsign']
        comments = request.form['comments']
        frequency = request.form['frequency']
        mode = request.form['mode']
        power = request.form['power']
        self_location = request.form['self_location']
        contact_location = request.form['contact_location']
        self_rst = request.form['self_rst']
        contact_rst = request.form['contact_rst']
        error = None

        if not callsign:
            error = 'callsign is required.'

        if not comments:
            error = 'comments are required'    

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO contacts (callsign, comments, author_id, frequency, mode, power, self_location, contact_location, self_rst, contact_rst)'
                ' VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (callsign, comments, g.user['id'])
            )
            db.commit()
            return redirect(url_for('log.index'))

    return render_template('log/create.html')    

def get_post(id, check_author=True):
    contact = get_db().execute(
        'SELECT p.id, callsign, comments, created, author_id, username, frequency, mode, power, self_location, contact_location, self_rst, contact_rst'
        ' FROM contacts p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if contact is None:
        abort(404, f"contacts id {id} doesn't exist.")

    if check_author and contact['author_id'] != g.user['id']:
        abort(403)

    return contact    

#update view
@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    contact = get_post(id)

    if request.method == 'POST':
        callsign = request.form['callsign']
        comments = request.form['comments']
        frequency = request.form['frequency']
        mode = request.form['mode']
        power = request.form['power']
        self_location = request.form['self_location']
        contact_location = request.form['contact_location']
        self_rst = request.form['self_rst']
        contact_rst = request.form['contact_rst']
        error = None

        #checks if callsign field is blank
        if not callsign:
            error = 'callsign is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE contacts SET callsign = ?, comments = ?, frequency = ?, mode = ?, power = ?, self_location = ?, contact_location = ?, self_rst = ?, contact_rst = ?'
                ' WHERE id = ?',
                (callsign, comments, frequency, mode, power, self_location, contact_location, self_rst, contact_rst, id)
            )
            db.commit()
            return redirect(url_for('log.index'))

    return render_template('log/update.html', contact=contact)    

#delete view
@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM contacts WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('log.index'))    