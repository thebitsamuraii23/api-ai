# Data Encryption Key Setup

## What Is `DATA_ENCRYPTION_KEY`?

`DATA_ENCRYPTION_KEY` is the symmetric encryption key used to protect sensitive data (such as user API keys) in this application.

The project uses **Fernet** from Python's `cryptography` package.

## How Encryption Works in This Bot

1. Initialization (`bot/db.py`):

```python
self._fernet = Fernet(encryption_key.encode("utf-8"))
```

2. Encryption:

- User API keys are encrypted before database persistence.
- Encrypted values are saved in the `api_keys` table.

3. Decryption:

- Values are decrypted only when the runtime needs to call a provider API.

## Generate a Key

### Option 1: Built-In Script (Recommended)

```bash
python generate_encryption_key.py
```

### Option 2: Generate Manually in Python

```python
from cryptography.fernet import Fernet

key = Fernet.generate_key()
print(key.decode("utf-8"))
```

A Fernet key looks like this:

```text
Z61uwbFoj79JdfTmcaZG28olbqQtf4VI_MpQuOcw6Y0=
```

## Where to Configure the Key

Set it in your `.env` file in the project root:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
DATA_ENCRYPTION_KEY=your_generated_fernet_key
DATABASE_PATH=data/bot.db
DEFAULT_LANGUAGE=en
DEFAULT_PROVIDER=openai
MEMORY_MESSAGES=20
```

## Security Guidelines

1. Keep the key secret.
- Never commit `.env` to Git.
- Store production secrets in a dedicated secret manager.

2. One key protects all encrypted records.
- If you lose the key, previously encrypted values cannot be decrypted.

3. Use environment-based secret delivery in production.
- Examples: AWS Secrets Manager, HashiCorp Vault, Doppler, 1Password Secrets Automation.

4. Do not alter key format.
- Fernet keys are fixed-length URL-safe Base64 values.

## Code Usage Example

```python
from bot.config import load_settings
from bot.db import Database

settings = load_settings()

db = Database(
    db_path=settings.database_path,
    encryption_key=settings.data_encryption_key,
    default_language=settings.default_language,
    default_provider=settings.default_provider,
)

await db.init()
```

## Validate the Key Quickly

```bash
python -c "
from cryptography.fernet import Fernet
import os
from dotenv import load_dotenv

load_dotenv()
key = os.getenv('DATA_ENCRYPTION_KEY')
try:
    Fernet(key.encode('utf-8'))
    print('Key is valid')
except Exception as e:
    print(f'Invalid key: {e}')
"
```

## Database Location of Encrypted Data

`api_keys.encrypted_key` stores encrypted API tokens.

```sql
CREATE TABLE api_keys (
    user_id INTEGER NOT NULL,
    provider TEXT NOT NULL,
    encrypted_key TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, provider),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
)
```

## FAQ

### Can I reuse one key across multiple projects?

It is possible, but not recommended. Use a separate encryption key per project.

### What if I lost the key?

Encrypted values cannot be recovered without the original key. Restore the key from your secrets backup.

### Can I rotate the key?

Yes, but rotation requires decrypt-and-reencrypt migration of existing encrypted records.

### Can I replace Fernet with another algorithm?

Yes, but you must update encryption/decryption logic in `bot/db.py` and migrate stored data safely.
