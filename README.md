# HamPy :radio: - Ham Radio Contact Tracker

![HamPy Banner](static/images/hampy_banner.png)

HamPy is a Flask web application that provides an intuitive and efficient way to track and log your ham radio contacts. Developed with care by
**Michael Gregoire**, this tool is for ham radio enthusiasts looking to organize their contacts.

## Features :star:

- **Contact Log:** Never miss out on any detail. Log each ham radio contact with ease.
- **Date of Contact:** Know exactly when you connected.
- **Callsign:** Track both your callsign and the one you connected with.
- **Frequency Used:** Stay on top of the frequencies you're tapping into.
- **Mode Used:** Whether it's FM, AM, or SSB, we've got you covered.
- **Power Used:** Keep tabs on the power levels you utilized.
- **Locations:** Log both your location and the location of your contact.
- **RST (Received Signal Strength Indication):** Know both your RST and the RST of the contact you connected with.
- **Comments:** A dedicated section to jot down any special comments or memories associated with each contact.

## Roadmap :world_map:

We're always looking to improve HamPy and bring more features to our users. Here's a sneak peek at what's coming:

- [x] Search functionality to find contacts quickly.
- [x] Ability to filter contact views.
- [ ] Integration with mapping tools to visually plot contacts.
- [ ] Multiple Users.
- [ ] And much more!

> Do you have a feature in mind? Feel free to open an issue, and we'll look into it!

## Documentation :book:

### Installation
1. Create and activate a virtual environment.
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
2. Install project dependencies.
   ```bash
   pip install -r requirements.txt
   ```

### Configuration

HamPy uses environment variables for runtime configuration:

- `SECRET_KEY`  
  - **Development:** optional. If omitted, HamPy uses a local-only fallback key (`dev-insecure-change-me`).
  - **Production (`HAMPY_ENV=production`): required.** Startup fails if `SECRET_KEY` is not set.
- `HAMPY_ENV`  
  - Optional environment selector (`development` by default).
  - Set to `production` to enforce production safety checks.
- `MEILISEARCH_URL`
  - Optional URL for contact search (`http://127.0.0.1:7700` by default).
- `MEILISEARCH_KEY` or `MEILI_MASTER_KEY`
  - Optional key for secured Meilisearch instances.

Example development configuration:

```bash
export HAMPY_ENV=development
export SECRET_KEY="replace-with-a-local-dev-secret"
```

Example production configuration:

```bash
export HAMPY_ENV=production
export SECRET_KEY="strong-random-secret-key"
```

### Usage
Start Meilisearch for fast contact search:

```bash
docker run -it --rm \
  -p 7700:7700 \
  -e MEILI_ENV='development' \
  -v $(pwd)/meili_data:/meili_data \
  getmeili/meilisearch:v1.37
```

Build the React frontend, initialize the database, sync search, and run the app:

```bash
python -m pip install -r requirements.txt
npm install
npm run build
flask --app Contacts init-db
flask --app Contacts sync-search
flask --app Contacts --debug run
```

Open `http://127.0.0.1:5000`, register a user, and start logging contacts.

If Meilisearch is not running, HamPy falls back to SQLite search so development
can continue, but Meilisearch should be running for the intended search
experience.

During frontend development, keep Flask running and rebuild the React bundle when
you change `static/app.js` or `static/app.css`:

```bash
npm run watch
```

---

## Contributing

While this is currently a personal project, I may open it up to contributions in the future.

## Credits

- **Developer:** Michael Gregoire

## License

[GNU GENERAL PUBLIC LICENSE]

---

Stay tuned for more updates and thank you for choosing HamPy for your ham radio tracking needs! :smile: :radio:
