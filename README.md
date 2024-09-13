# RelaySMS Email Bridge

**RelaySMS Email Bridge** enables users to send emails when they don’t have direct access to their email account but need to communicate. The tool uses the sender’s phone number as an email alias. The email is relayed to the recipient with the sender’s phone number as the prefix and the bridge server’s hostname as the domain (e.g., `237123456789@relaysms.me`). This allows the recipient to identify the sender based on their phone number.

## Prerequisites

Before you begin, ensure you have:

1. **[Python 3.10+](https://www.python.org/downloads/)** installed.
2. **Python `venv` module** for creating virtual environments (included in Python 3.3+). [Learn more](https://docs.python.org/3/library/venv.html).
3. A valid **[SimpleLogin](https://simplelogin.io/)** account.

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/smswithoutborders/email-bridge.git
   cd email-bridge
   ```

2. **Set up a virtual environment:**

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**

   Set the required environment variables, either in a `.env` file or directly in your shell:

   - `SL_API_KEY`: SimpleLogin API key.
   - `SL_API_BASE_URL`: (default: `https://app.simplelogin.io/api`).
   - `SL_PRIMARY_EMAIL`: Your primary SimpleLogin email.
   - `SL_PRIMARY_DOMAIN`: Your SimpleLogin domain.
   - `BRIDGE_SMTP_SERVER`: SMTP server address linked to `SL_PRIMARY_EMAIL`.
   - `BRIDGE_SMTP_PORT`: SMTP server port (default: `587`).
   - `BRIDGE_SMTP_USERNAME`: Your SMTP username.
   - `BRIDGE_SMTP_PASSWORD`: Your SMTP password.
   - `BRIDGE_SMTP_ENABLE_TLS`: Enable TLS (default: `True`).

   Example:

   ```bash
   export SL_API_KEY="your-api-key"
   export SL_PRIMARY_EMAIL="you@example.com"
   export SL_PRIMARY_DOMAIN="example.com"
   export BRIDGE_SMTP_SERVER="smtp.example.com"
   export BRIDGE_SMTP_PORT=587
   export BRIDGE_SMTP_USERNAME="your-username"
   export BRIDGE_SMTP_PASSWORD="your-password"
   ```

## Clients

### SimpleLogin Email Client

This client uses SimpleLogin to manage aliases and reverse aliases for sending emails.

## Usage

To send an email using a phone number alias, use the following command:

```bash
python3 -m simplelogin.client send_email \
  --phone_number +237123456789 \
  --to recipient@example.com \
  --subject "Subject Here" \
  --body "Email body content here." \
  [--cc cc@example.com] \
  [--bcc bcc@example.com]
```

### Command Arguments

- `--phone_number`: The phone number to generate or retrieve an email alias.
- `--to`: Recipient’s email address.
- `--subject`: Email subject.
- `--body`: Email body content.
- `--cc`: (Optional) CC email address.
- `--bcc`: (Optional) BCC email address.

### Example

```bash
python3 -m simplelogin.client send_email \
  --phone_number +237123456789 \
  --to recipient@example.com \
  --subject "Greetings" \
  --body "Hello, this is a test email."
```

## Logging

Set the log level by configuring the `LOG_LEVEL` environment variable. Default is `INFO`.

## Contributing

To contribute:

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature-branch`.
3. Commit your changes: `git commit -m 'Add a new feature'`.
4. Push to the branch: `git push origin feature-branch`.
5. Open a Pull Request.

## License

This project is licensed under the GNU General Public License (GPL). See the [LICENSE](LICENSE) file for details.
