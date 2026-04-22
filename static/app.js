import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  CalendarDays,
  LockKeyhole,
  LogOut,
  MapPin,
  Pencil,
  Plus,
  Radio,
  RefreshCw,
  Save,
  Search,
  Signal,
  Trash2,
  UserRound,
  X,
  Zap,
} from 'lucide-react';

const h = React.createElement;

const emptyContact = {
  callsign: '',
  frequency: '',
  mode: '',
  power: '',
  self_location: '',
  contact_location: '',
  self_rst: '',
  contact_rst: '',
  comments: '',
};

async function api(path, options = {}) {
  const response = await fetch(path, {
    credentials: 'same-origin',
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  });
  const payload = await response.json().catch(() => ({}));

  if (!response.ok) {
    const message = payload.error || Object.values(payload.errors || {})[0] || 'Request failed.';
    throw new Error(message);
  }

  return payload;
}

function iconNode(Icon, className = 'icon') {
  return h(Icon, { className, 'aria-hidden': true, strokeWidth: 2 });
}

function formatDate(value) {
  if (!value) return 'No date';
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value.slice(0, 10);
  return new Intl.DateTimeFormat(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  }).format(parsed);
}

function contactBand(contact) {
  const frequency = Number(contact.frequency);
  if (!frequency) return 'Unset';

  if (frequency >= 1800 && frequency <= 2000) return '160m';
  if (frequency >= 3500 && frequency <= 4000) return '80m';
  if (frequency >= 5330 && frequency <= 5410) return '60m';
  if (frequency >= 7000 && frequency <= 7300) return '40m';
  if (frequency >= 10100 && frequency <= 10150) return '30m';
  if (frequency >= 14000 && frequency <= 14350) return '20m';
  if (frequency >= 18068 && frequency <= 18168) return '17m';
  if (frequency >= 21000 && frequency <= 21450) return '15m';
  if (frequency >= 24890 && frequency <= 24990) return '12m';
  if (frequency >= 28000 && frequency <= 29700) return '10m';
  if (frequency >= 50000 && frequency <= 54000) return '6m';
  if (frequency >= 144000 && frequency <= 148000) return '2m';
  if (frequency >= 420000 && frequency <= 450000) return '70cm';
  return 'Other';
}

function dateValue(value) {
  if (!value) return '';
  return String(value).slice(0, 10);
}

function AuthPanel({ onAuth }) {
  const [mode, setMode] = useState('login');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  async function submit(event) {
    event.preventDefault();
    setError('');
    setBusy(true);

    try {
      const path = mode === 'login' ? '/api/auth/login' : '/api/auth/register';
      const payload = await api(path, {
        method: 'POST',
        body: JSON.stringify({ username, password }),
      });
      onAuth(payload.user);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return h('main', { className: 'auth-layout' },
    h('section', { className: 'brand-panel' },
      h('div', { className: 'brand-bar' },
        h('div', { className: 'brand-mark' }, iconNode(Radio)),
        h('div', null,
          h('p', { className: 'eyebrow' }, 'HamPy Operations Console'),
          h('h1', null, 'Logbook command center for the radio desk')
        )
      ),
      h('div', { className: 'command-strip', 'aria-label': 'Station status' },
        h('span', null, 'DX WATCH'),
        h('span', null, 'LOCAL LOG'),
        h('span', null, 'FAST QSO ENTRY'),
        h('span', null, 'DARK SHACK MODE')
      ),
      h('div', { className: 'signal-card' },
        h('img', {
          src: '/static/images/hampy_banner.png',
          alt: 'HamPy radio contact tracker banner',
        }),
        h('div', { className: 'signal-readout' },
          h('span', null, 'HF READY'),
          h('span', null, 'QSO LOG'),
          h('span', null, 'RST 59')
        )
      )
    ),
    h('section', { className: 'auth-card', 'aria-label': 'Authentication' },
      h('div', { className: 'segmented' },
        h('button', {
          className: mode === 'login' ? 'active' : '',
          onClick: () => setMode('login'),
          type: 'button',
        }, 'Log in'),
        h('button', {
          className: mode === 'register' ? 'active' : '',
          onClick: () => setMode('register'),
          type: 'button',
        }, 'Register')
      ),
      h('form', { onSubmit: submit },
        h('label', null,
          h('span', null, 'Username'),
          h('div', { className: 'field' },
            iconNode(UserRound),
            h('input', {
              autoComplete: 'username',
              onChange: event => setUsername(event.target.value),
              required: true,
              value: username,
            })
          )
        ),
        h('label', null,
          h('span', null, 'Password'),
          h('div', { className: 'field' },
            iconNode(LockKeyhole),
            h('input', {
              autoComplete: mode === 'login' ? 'current-password' : 'new-password',
              onChange: event => setPassword(event.target.value),
              required: true,
              type: 'password',
              value: password,
            })
          )
        ),
        error && h('p', { className: 'form-error' }, error),
        h('button', { className: 'primary-action', disabled: busy, type: 'submit' },
          busy ? 'Working...' : mode === 'login' ? 'Open Log' : 'Create Account'
        )
      )
    )
  );
}

function StatCard({ icon, label, value, tone }) {
  return h('article', { className: `stat-card ${tone}` },
    h('div', { className: 'stat-icon' }, icon),
    h('div', null,
      h('p', null, label),
      h('strong', null, value)
    )
  );
}

function ContactForm({ contact, onCancel, onSaved }) {
  const [values, setValues] = useState(contact || emptyContact);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const isEditing = Boolean(contact?.id);

  function update(name, value) {
    setValues(current => ({ ...current, [name]: value }));
  }

  async function submit(event) {
    event.preventDefault();
    setError('');
    setBusy(true);

    try {
      const payload = await api(isEditing ? `/api/contacts/${contact.id}` : '/api/contacts', {
        method: isEditing ? 'PUT' : 'POST',
        body: JSON.stringify(values),
      });
      onSaved(payload.contact);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return h('aside', { className: 'editor-panel', 'aria-label': isEditing ? 'Edit contact' : 'New contact' },
    h('div', { className: 'panel-header' },
      h('div', null,
        h('p', { className: 'eyebrow' }, isEditing ? 'Edit QSO' : 'New QSO'),
        h('h2', null, isEditing ? values.callsign : 'Log a contact')
      ),
      h('button', { className: 'icon-button', onClick: onCancel, type: 'button', title: 'Close editor' }, iconNode(X))
    ),
    h('form', { className: 'contact-form', onSubmit: submit },
      h('div', { className: 'form-grid' },
        inputField('Callsign', 'callsign', values, update, { required: true }),
        inputField('Frequency', 'frequency', values, update, { inputMode: 'numeric', placeholder: '146520' }),
        inputField('Mode', 'mode', values, update, { placeholder: 'FM' }),
        inputField('Power', 'power', values, update, { inputMode: 'numeric', placeholder: '50' }),
        inputField('Your location', 'self_location', values, update, { placeholder: 'Boston, MA' }),
        inputField('Their location', 'contact_location', values, update, { placeholder: 'Providence, RI' }),
        inputField('Your RST', 'self_rst', values, update, { inputMode: 'numeric', placeholder: '59' }),
        inputField('Their RST', 'contact_rst', values, update, { inputMode: 'numeric', placeholder: '57' })
      ),
      h('label', { className: 'full-field' },
        h('span', null, 'Comments'),
        h('textarea', {
          onChange: event => update('comments', event.target.value),
          required: true,
          rows: 4,
          value: values.comments || '',
        })
      ),
      error && h('p', { className: 'form-error' }, error),
      h('div', { className: 'form-actions' },
        h('button', { className: 'secondary-action', onClick: onCancel, type: 'button' }, 'Cancel'),
        h('button', { className: 'primary-action', disabled: busy, type: 'submit' },
          iconNode(Save),
          busy ? 'Saving...' : 'Save Contact'
        )
      )
    )
  );
}

function inputField(label, name, values, update, options = {}) {
  return h('label', null,
    h('span', null, label),
    h('input', {
      inputMode: options.inputMode,
      onChange: event => update(name, event.target.value),
      placeholder: options.placeholder,
      required: options.required,
      value: values[name] ?? '',
    })
  );
}

function ContactRow({ contact, onEdit, onDelete }) {
  return h('article', { className: 'contact-row' },
    h('div', { className: 'contact-main' },
      h('div', { className: 'callsign-block' },
        h('span', { className: 'pulse-dot' }),
        h('div', null,
          h('h3', null, contact.callsign),
          h('p', null, contact.comments)
        )
      ),
      h('div', { className: 'contact-meta' },
        h('span', null, iconNode(CalendarDays), formatDate(contact.created)),
        h('span', null, iconNode(Radio), contact.frequency || 'Open freq'),
        h('span', null, iconNode(Signal), contact.mode || 'Mode unset')
      )
    ),
    h('div', { className: 'contact-detail-grid' },
      detail('Power', contact.power ? `${contact.power} W` : 'Unset'),
      detail('Your RST', contact.self_rst || 'Unset'),
      detail('Their RST', contact.contact_rst || 'Unset'),
      detail('Path', [contact.self_location, contact.contact_location].filter(Boolean).join(' -> ') || 'Locations unset')
    ),
    h('div', { className: 'row-actions' },
      h('button', { className: 'icon-button', onClick: () => onEdit(contact), type: 'button', title: 'Edit contact' }, iconNode(Pencil)),
      h('button', { className: 'icon-button danger', onClick: () => onDelete(contact), type: 'button', title: 'Delete contact' }, iconNode(Trash2))
    )
  );
}

function detail(label, value) {
  return h('div', { className: 'detail-item' },
    h('span', null, label),
    h('strong', null, value)
  );
}

function Dashboard({ user, onLogout }) {
  const [contacts, setContacts] = useState([]);
  const [totalContacts, setTotalContacts] = useState(0);
  const [query, setQuery] = useState('');
  const [mode, setMode] = useState('all');
  const [filters, setFilters] = useState({
    band: 'all',
    dateFrom: '',
    dateTo: '',
    location: '',
    minRst: '',
  });
  const [editorContact, setEditorContact] = useState(null);
  const [editorOpen, setEditorOpen] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  async function loadContacts(searchValue = query) {
    setError('');
    setLoading(true);
    try {
      const queryString = searchValue.trim()
        ? `?q=${encodeURIComponent(searchValue.trim())}`
        : '';
      const payload = await api(`/api/contacts${queryString}`);
      setContacts(payload.contacts);
      setTotalContacts(payload.total_contacts ?? payload.contacts.length);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const searchTimer = window.setTimeout(() => {
      loadContacts(query);
    }, 220);

    return () => window.clearTimeout(searchTimer);
  }, [query]);

  const modes = useMemo(() => {
    const names = contacts.map(contact => contact.mode).filter(Boolean);
    return ['all', ...Array.from(new Set(names)).sort()];
  }, [contacts]);

  const bands = useMemo(() => {
    const names = contacts.map(contactBand).filter(band => band !== 'Unset');
    return ['all', ...Array.from(new Set(names)).sort((a, b) => a.localeCompare(b, undefined, { numeric: true }))];
  }, [contacts]);

  const activeFilterCount = useMemo(() => {
    return [
      query.trim(),
      mode !== 'all',
      filters.band !== 'all',
      filters.dateFrom,
      filters.dateTo,
      filters.location.trim(),
      filters.minRst,
    ].filter(Boolean).length;
  }, [filters, mode, query]);

  const filtered = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    const locationQuery = filters.location.trim().toLowerCase();
    const minimumRst = Number(filters.minRst);
    return contacts.filter(contact => {
      const modeMatch = mode === 'all' || contact.mode === mode;
      const bandMatch = filters.band === 'all' || contactBand(contact) === filters.band;
      const contactDate = dateValue(contact.created);
      const fromMatch = !filters.dateFrom || contactDate >= filters.dateFrom;
      const toMatch = !filters.dateTo || contactDate <= filters.dateTo;
      const locationText = [contact.self_location, contact.contact_location].join(' ').toLowerCase();
      const locationMatch = !locationQuery || locationText.includes(locationQuery);
      const rstValues = [Number(contact.self_rst), Number(contact.contact_rst)].filter(Number.isFinite);
      const rstMatch = !filters.minRst || rstValues.some(rst => rst >= minimumRst);
      const text = [
        contact.callsign,
        contact.comments,
        contact.frequency,
        contact.mode,
        contact.self_location,
        contact.contact_location,
      ].join(' ').toLowerCase();
      return modeMatch
        && bandMatch
        && fromMatch
        && toMatch
        && locationMatch
        && rstMatch
        && (!normalized || text.includes(normalized));
    });
  }, [contacts, filters, mode, query]);

  const stats = useMemo(() => {
    const power = contacts.reduce((sum, contact) => sum + (Number(contact.power) || 0), 0);
    const uniqueModes = new Set(contacts.map(contact => contact.mode).filter(Boolean)).size;
    return { power, uniqueModes };
  }, [contacts]);

  function startCreate() {
    setEditorContact(null);
    setEditorOpen(true);
  }

  function startEdit(contact) {
    setEditorContact(contact);
    setEditorOpen(true);
  }

  function updateFilter(name, value) {
    setFilters(current => ({ ...current, [name]: value }));
  }

  function clearFilters() {
    setQuery('');
    setMode('all');
    setFilters({
      band: 'all',
      dateFrom: '',
      dateTo: '',
      location: '',
      minRst: '',
    });
  }

  function saveContact(saved) {
    setContacts(current => {
      const exists = current.some(contact => contact.id === saved.id);
      if (exists) {
        return current.map(contact => contact.id === saved.id ? saved : contact);
      }
      return [saved, ...current];
    });
    setTotalContacts(current => editorContact?.id ? current : current + 1);
    setEditorOpen(false);
    setEditorContact(null);
    loadContacts(query);
  }

  async function deleteContact(contact) {
    const confirmed = window.confirm(`Delete ${contact.callsign}?`);
    if (!confirmed) return;

    try {
      await api(`/api/contacts/${contact.id}`, { method: 'DELETE' });
      setContacts(current => current.filter(item => item.id !== contact.id));
      setTotalContacts(current => Math.max(0, current - 1));
    } catch (err) {
      setError(err.message);
    }
  }

  async function logout() {
    await api('/api/auth/logout', { method: 'POST' });
    onLogout();
  }

  return h('main', { className: 'app-shell' },
    h('header', { className: 'topbar' },
      h('div', { className: 'brand-compact' },
        h('div', { className: 'brand-mark' }, iconNode(Radio)),
        h('div', null,
          h('strong', null, 'HamPy'),
          h('span', null, `Operator ${user.username} / local station`)
        )
      ),
      h('div', { className: 'topbar-actions' },
        h('button', { className: 'secondary-action', onClick: loadContacts, type: 'button' }, iconNode(RefreshCw), 'Refresh'),
        h('button', { className: 'secondary-action', onClick: logout, type: 'button' }, iconNode(LogOut), 'Log out')
      )
    ),
    h('section', { className: 'dashboard-grid' },
      h('section', { className: 'workspace' },
        h('div', { className: 'ops-strip' },
          h('span', null, 'LOGBOOK ONLINE'),
          h('span', null, `${totalContacts} QSO${totalContacts === 1 ? '' : 'S'}`),
          h('span', null, `${filtered.length} IN VIEW`),
          h('span', null, activeFilterCount ? `${activeFilterCount} FILTER${activeFilterCount === 1 ? '' : 'S'} ACTIVE` : 'UNFILTERED VIEW')
        ),
        h('div', { className: 'workspace-header' },
          h('div', null,
            h('p', { className: 'eyebrow' }, 'Operator Console'),
            h('h1', null, 'QSO Control')
          ),
          h('button', { className: 'primary-action', onClick: startCreate, type: 'button' }, iconNode(Plus), 'New Contact')
        ),
        h('div', { className: 'stats-grid' },
          h(StatCard, { icon: iconNode(Radio), label: 'Contacts', value: totalContacts, tone: 'blue' }),
          h(StatCard, { icon: iconNode(Signal), label: 'Modes', value: stats.uniqueModes, tone: 'green' }),
          h(StatCard, { icon: iconNode(Zap), label: 'Logged Watts', value: stats.power, tone: 'amber' }),
          h(StatCard, { icon: iconNode(MapPin), label: 'Visible', value: filtered.length, tone: 'red' })
        ),
        h('div', { className: 'toolbar' },
          h('label', { className: 'search-field' },
            iconNode(Search),
            h('input', {
              onChange: event => setQuery(event.target.value),
              placeholder: 'Search callsign, mode, location, comments',
              value: query,
            })
          ),
          h('div', { className: 'mode-tabs' },
            modes.map(item => h('button', {
              className: mode === item ? 'active' : '',
              key: item,
              onClick: () => setMode(item),
              type: 'button',
            }, item === 'all' ? 'All' : item))
          )
        ),
        h('section', { className: 'filter-deck', 'aria-label': 'Contact view filters' },
          h('label', null,
            h('span', null, 'Band'),
            h('select', {
              onChange: event => updateFilter('band', event.target.value),
              value: filters.band,
            },
              bands.map(band => h('option', { key: band, value: band }, band === 'all' ? 'All bands' : band))
            )
          ),
          h('label', null,
            h('span', null, 'From'),
            h('input', {
              onChange: event => updateFilter('dateFrom', event.target.value),
              type: 'date',
              value: filters.dateFrom,
            })
          ),
          h('label', null,
            h('span', null, 'To'),
            h('input', {
              onChange: event => updateFilter('dateTo', event.target.value),
              type: 'date',
              value: filters.dateTo,
            })
          ),
          h('label', null,
            h('span', null, 'Location'),
            h('input', {
              onChange: event => updateFilter('location', event.target.value),
              placeholder: 'Grid, city, state',
              value: filters.location,
            })
          ),
          h('label', null,
            h('span', null, 'Min RST'),
            h('input', {
              inputMode: 'numeric',
              onChange: event => updateFilter('minRst', event.target.value),
              placeholder: '57',
              value: filters.minRst,
            })
          ),
          h('button', {
            className: 'secondary-action clear-filters',
            disabled: !activeFilterCount,
            onClick: clearFilters,
            type: 'button',
          }, 'Clear Filters')
        ),
        error && h('p', { className: 'form-error' }, error),
        h('section', { className: 'contact-list', 'aria-live': 'polite' },
          loading
            ? h('div', { className: 'empty-state' }, 'Loading contacts...')
            : filtered.length
              ? filtered.map(contact => h(ContactRow, {
                contact,
                key: contact.id,
                onDelete: deleteContact,
                onEdit: startEdit,
              }))
              : h('div', { className: 'empty-state' },
                h('strong', null, contacts.length ? 'No contacts match this view.' : 'No contacts logged yet.'),
                h('span', null, contacts.length ? 'Adjust the search or mode filter.' : 'Create your first contact to populate the dashboard.')
              )
        )
      ),
      editorOpen
        ? h(ContactForm, {
          contact: editorContact,
          onCancel: () => setEditorOpen(false),
          onSaved: saveContact,
        })
        : h('aside', { className: 'insight-panel' },
          h('p', { className: 'eyebrow' }, 'Signal Watch'),
          h('h2', null, contacts[0]?.callsign || 'Ready to transmit'),
          h('p', null, contacts[0]?.comments || 'Your newest contact details will stay within reach here once the log starts filling in.'),
          h('div', { className: 'watch-grid' },
            detail('Last mode', contacts[0]?.mode || 'Standby'),
            detail('Last freq', contacts[0]?.frequency || 'Unset'),
            detail('Watts logged', stats.power || '0'),
            detail('Mode filters', stats.uniqueModes || '0')
          ),
          h('div', { className: 'mini-spectrum', 'aria-hidden': true },
            Array.from({ length: 18 }, (_, index) => h('span', {
              key: index,
              style: { height: `${24 + ((index * 17) % 58)}px` },
            }))
          )
        )
    )
  );
}

function App() {
  const [user, setUser] = useState(null);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    api('/api/session')
      .then(payload => setUser(payload.user))
      .finally(() => setChecking(false));
  }, []);

  if (checking) {
    return h('main', { className: 'loading-screen' },
      h('div', { className: 'brand-mark' }, iconNode(Radio)),
      h('span', null, 'Tuning HamPy...')
    );
  }

  return user
    ? h(Dashboard, { user, onLogout: () => setUser(null) })
    : h(AuthPanel, { onAuth: setUser });
}

createRoot(document.getElementById('root')).render(h(App));
