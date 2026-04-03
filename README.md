# HamPy :radio: - Ham Radio Contact Tracker

![HamPy Banner](Contacts/static/images/hampy_banner.png)

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

- [ ] Search functionality to find contacts quickly.
- [ ] Ability to filter contact views.
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
2. Install project dependencies and the local package in editable mode.
   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

### Configuration

HamPy uses environment variables for runtime configuration:

- `SECRET_KEY`  
  - **Development:** optional. If omitted, HamPy uses a local-only fallback key (`dev-insecure-change-me`).
  - **Production (`HAMPY_ENV=production`): required.** Startup fails if `SECRET_KEY` is not set.
- `HAMPY_ENV`  
  - Optional environment selector (`development` by default).
  - Set to `production` to enforce production safety checks.

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

### Canonical Flask app entrypoint

HamPy's canonical Flask entrypoint is:

```bash
Contacts:create_app
```

Use this exact value with `flask --app ...` for all CLI commands so local development and deployment scripts stay aligned.

### Usage
Initialize the database and run the app:

```bash
flask --app Contacts:create_app init-db
flask --app Contacts:create_app run --debug
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
