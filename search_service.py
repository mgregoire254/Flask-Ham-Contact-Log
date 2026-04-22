import os

import click
from flask import current_app

from Contacts.db import get_db


INDEX_NAME = 'contacts'


def _client():
    try:
        import meilisearch
    except ImportError:
        return None

    url = os.environ.get('MEILISEARCH_URL', 'http://127.0.0.1:7700')
    key = os.environ.get('MEILISEARCH_KEY', os.environ.get('MEILI_MASTER_KEY'))
    return meilisearch.Client(url, key)


def _index(client):
    index_name = current_app.config.get('MEILISEARCH_INDEX', INDEX_NAME)
    return client.index(index_name)


def _document(contact):
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


def _wait_for_task(client, task):
    task_uid = getattr(task, 'task_uid', None)
    if task_uid is None and isinstance(task, dict):
        task_uid = task.get('taskUid') or task.get('task_uid')

    if task_uid is not None:
        client.wait_for_task(task_uid)


def is_available():
    client = _client()
    if client is None:
        return False

    try:
        client.health()
    except Exception:
        return False

    return True


def configure_index(wait=False):
    client = _client()
    if client is None:
        return False

    try:
        index = _index(client)
        task = index.update_filterable_attributes(['author_id', 'mode'])
        if wait:
            _wait_for_task(client, task)
        task = index.update_sortable_attributes(['created'])
        if wait:
            _wait_for_task(client, task)
    except Exception:
        return False

    return True


def sync_contacts(wait=False):
    client = _client()
    if client is None:
        return False

    try:
        configure_index(wait=wait)
        contacts = get_db().execute(
            'SELECT p.id, callsign, comments, created, author_id, username, frequency, mode, power, self_location, contact_location, self_rst, contact_rst'
            ' FROM contacts p JOIN user u ON p.author_id = u.id'
        ).fetchall()
        documents = [_document(contact) for contact in contacts]
        task = _index(client).add_documents(documents)
        if wait:
            _wait_for_task(client, task)
    except Exception:
        return False

    return True


def sync_contact(contact_id, wait=False):
    client = _client()
    if client is None:
        return False

    try:
        configure_index(wait=wait)
        contact = get_db().execute(
            'SELECT p.id, callsign, comments, created, author_id, username, frequency, mode, power, self_location, contact_location, self_rst, contact_rst'
            ' FROM contacts p JOIN user u ON p.author_id = u.id'
            ' WHERE p.id = ?',
            (contact_id,),
        ).fetchone()
        if contact is None:
            return delete_contact(contact_id, wait=wait)

        task = _index(client).add_documents([_document(contact)])
        if wait:
            _wait_for_task(client, task)
    except Exception:
        return False

    return True


def delete_contact(contact_id, wait=False):
    client = _client()
    if client is None:
        return False

    try:
        task = _index(client).delete_document(contact_id)
        if wait:
            _wait_for_task(client, task)
    except Exception:
        return False

    return True


def search_contact_ids(query, author_id, limit=200):
    query = (query or '').strip()
    if not query:
        return None

    client = _client()
    if client is None:
        return None

    try:
        configure_index()
        results = _index(client).search(
            query,
            {
                'filter': f'author_id = {int(author_id)}',
                'limit': limit,
                'attributesToRetrieve': ['id'],
            },
        )
    except Exception:
        return None

    return [hit['id'] for hit in results.get('hits', [])]


@click.command('sync-search')
def sync_search_command():
    """Sync all SQLite contacts into Meilisearch."""
    if sync_contacts(wait=True):
        click.echo('Synced contacts into Meilisearch.')
    else:
        click.echo(
            'Meilisearch is unavailable. Start it and run this command again.',
            err=True,
        )


def init_app(app):
    app.cli.add_command(sync_search_command)
