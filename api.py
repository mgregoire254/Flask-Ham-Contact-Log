import sqlite3

from flask import Blueprint, g, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from Contacts.db import get_db
from Contacts import search_service


bp = Blueprint('api', __name__, url_prefix='/api')


def _current_user_payload():
    if g.user is None:
        return None

    return {
        'id': g.user['id'],
        'username': g.user['username'],
    }


def _contact_payload(contact):
    return {
        'id': contact['id'],
        'author_id': contact['author_id'],
        'username': contact['username'],
        'created': contact['created'].isoformat()
        if hasattr(contact['created'], 'isoformat')
        else str(contact['created']),
        'callsign': contact['callsign'],
        'frequency': contact['frequency'],
        'mode': contact['mode'],
        'power': contact['power'],
        'comments': contact['comments'],
        'self_location': contact['self_location'],
        'contact_location': contact['contact_location'],
        'self_rst': contact['self_rst'],
        'contact_rst': contact['contact_rst'],
    }


def _json_data():
    return request.get_json(silent=True) or {}


def _clean_text(value):
    if value is None:
        return ''
    return str(value).strip()


def _clean_optional_int(value):
    if value is None or value == '':
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _require_user():
    if g.user is None:
        return jsonify({'error': 'Authentication required.'}), 401
    return None


def _get_contact(contact_id, check_author=True):
    contact = get_db().execute(
        'SELECT p.id, callsign, comments, created, author_id, username, frequency, mode, power, self_location, contact_location, self_rst, contact_rst'
        ' FROM contacts p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (contact_id,),
    ).fetchone()

    if contact is None:
        return None, (jsonify({'error': 'Contact not found.'}), 404)

    if check_author and contact['author_id'] != g.user['id']:
        return None, (jsonify({'error': 'You cannot modify this contact.'}), 403)

    return contact, None


def _contact_values(data):
    callsign = _clean_text(data.get('callsign')).upper()
    comments = _clean_text(data.get('comments'))
    values = {
        'callsign': callsign,
        'comments': comments,
        'frequency': _clean_optional_int(data.get('frequency')),
        'mode': _clean_text(data.get('mode')).upper(),
        'power': _clean_optional_int(data.get('power')),
        'self_location': _clean_text(data.get('self_location')),
        'contact_location': _clean_text(data.get('contact_location')),
        'self_rst': _clean_optional_int(data.get('self_rst')),
        'contact_rst': _clean_optional_int(data.get('contact_rst')),
    }
    errors = {}

    if not callsign:
        errors['callsign'] = 'Callsign is required.'
    if not comments:
        errors['comments'] = 'Comments are required.'

    return values, errors


def _contacts_query(search_term):
    sql = (
        'SELECT p.id, callsign, comments, created, author_id, username, frequency, mode, power, self_location, contact_location, self_rst, contact_rst'
        ' FROM contacts p JOIN user u ON p.author_id = u.id'
        ' WHERE p.author_id = ?'
    )
    params = [g.user['id']]

    if search_term:
        searchable_columns = (
            'callsign',
            'comments',
            'CAST(frequency AS TEXT)',
            'mode',
            'CAST(power AS TEXT)',
            'self_location',
            'contact_location',
            'CAST(self_rst AS TEXT)',
            'CAST(contact_rst AS TEXT)',
        )
        sql += ' AND (' + ' OR '.join(
            f"LOWER(COALESCE({column}, '')) LIKE ?" for column in searchable_columns
        ) + ')'
        params.extend([f'%{search_term.lower()}%'] * len(searchable_columns))

    sql += ' ORDER BY created DESC'
    return sql, params


@bp.get('/session')
def session_status():
    return jsonify({'user': _current_user_payload()})


@bp.post('/auth/register')
def register():
    data = _json_data()
    username = _clean_text(data.get('username'))
    password = data.get('password') or ''

    if not username:
        return jsonify({'error': 'Username is required.'}), 400
    if not password:
        return jsonify({'error': 'Password is required.'}), 400

    try:
        db = get_db()
        db.execute(
            'INSERT INTO user (username, password) VALUES (?, ?)',
            (username, generate_password_hash(password)),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify({'error': f'User {username} is already registered.'}), 409

    session.clear()
    user = get_db().execute(
        'SELECT * FROM user WHERE username = ?',
        (username,),
    ).fetchone()
    session['user_id'] = user['id']
    g.user = user
    return jsonify({'user': _current_user_payload()}), 201


@bp.post('/auth/login')
def login():
    data = _json_data()
    username = _clean_text(data.get('username'))
    password = data.get('password') or ''

    user = get_db().execute(
        'SELECT * FROM user WHERE username = ?',
        (username,),
    ).fetchone()

    if user is None or not check_password_hash(user['password'], password):
        return jsonify({'error': 'Incorrect username or password.'}), 401

    session.clear()
    session['user_id'] = user['id']
    g.user = user
    return jsonify({'user': _current_user_payload()})


@bp.post('/auth/logout')
def logout():
    session.clear()
    return jsonify({'user': None})


@bp.get('/contacts')
def contacts_index():
    unauthorized = _require_user()
    if unauthorized:
        return unauthorized

    search_term = _clean_text(request.args.get('q'))
    total_contacts = get_db().execute(
        'SELECT COUNT(*) FROM contacts WHERE author_id = ?',
        (g.user['id'],),
    ).fetchone()[0]
    search_ids = search_service.search_contact_ids(search_term, g.user['id'])

    if search_term and search_ids is not None:
        if search_ids:
            placeholders = ', '.join('?' for _ in search_ids)
            contacts = get_db().execute(
                'SELECT p.id, callsign, comments, created, author_id, username, frequency, mode, power, self_location, contact_location, self_rst, contact_rst'
                ' FROM contacts p JOIN user u ON p.author_id = u.id'
                f' WHERE p.author_id = ? AND p.id IN ({placeholders})',
                [g.user['id'], *search_ids],
            ).fetchall()
            contact_by_id = {contact['id']: contact for contact in contacts}
            contacts = [contact_by_id[id] for id in search_ids if id in contact_by_id]
        else:
            contacts = []
    else:
        sql, params = _contacts_query(search_term)
        contacts = get_db().execute(sql, params).fetchall()

    return jsonify({
        'contacts': [_contact_payload(contact) for contact in contacts],
        'query': search_term,
        'search_backend': 'meilisearch' if search_term and search_ids is not None else 'sqlite',
        'total_contacts': total_contacts,
    })


@bp.post('/contacts')
def contacts_create():
    unauthorized = _require_user()
    if unauthorized:
        return unauthorized

    values, errors = _contact_values(_json_data())
    if errors:
        return jsonify({'errors': errors}), 400

    db = get_db()
    cursor = db.execute(
        'INSERT INTO contacts (callsign, comments, author_id, frequency, mode, power, self_location, contact_location, self_rst, contact_rst)'
        ' VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
        (
            values['callsign'],
            values['comments'],
            g.user['id'],
            values['frequency'],
            values['mode'],
            values['power'],
            values['self_location'],
            values['contact_location'],
            values['self_rst'],
            values['contact_rst'],
        ),
    )
    db.commit()
    search_service.sync_contact(cursor.lastrowid)

    contact, error = _get_contact(cursor.lastrowid)
    if error:
        return error
    return jsonify({'contact': _contact_payload(contact)}), 201


@bp.put('/contacts/<int:contact_id>')
def contacts_update(contact_id):
    unauthorized = _require_user()
    if unauthorized:
        return unauthorized

    contact, error = _get_contact(contact_id)
    if error:
        return error

    values, errors = _contact_values(_json_data())
    if errors:
        return jsonify({'errors': errors}), 400

    db = get_db()
    db.execute(
        'UPDATE contacts SET callsign = ?, comments = ?, frequency = ?, mode = ?, power = ?, self_location = ?, contact_location = ?, self_rst = ?, contact_rst = ?'
        ' WHERE id = ?',
        (
            values['callsign'],
            values['comments'],
            values['frequency'],
            values['mode'],
            values['power'],
            values['self_location'],
            values['contact_location'],
            values['self_rst'],
            values['contact_rst'],
            contact['id'],
        ),
    )
    db.commit()
    search_service.sync_contact(contact['id'])

    contact, error = _get_contact(contact_id)
    if error:
        return error
    return jsonify({'contact': _contact_payload(contact)})


@bp.delete('/contacts/<int:contact_id>')
def contacts_delete(contact_id):
    unauthorized = _require_user()
    if unauthorized:
        return unauthorized

    contact, error = _get_contact(contact_id)
    if error:
        return error

    db = get_db()
    db.execute('DELETE FROM contacts WHERE id = ?', (contact['id'],))
    db.commit()
    search_service.delete_contact(contact['id'])
    return jsonify({'deleted': True})
