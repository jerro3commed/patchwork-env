# patchwork-env

> CLI tool to diff and sync environment variables across multiple `.env` files and deployment targets.

---

## Installation

```bash
pip install patchwork-env
```

Or with [pipx](https://pypa.github.io/pipx/):

```bash
pipx install patchwork-env
```

---

## Usage

**Diff two `.env` files:**

```bash
patchwork-env diff .env.local .env.production
```

**Sync missing variables from one file to another:**

```bash
patchwork-env sync .env.local .env.production
```

**Check all deployment targets against a base file:**

```bash
patchwork-env audit .env.base --targets staging production
```

Example output:

```
[+] API_KEY       found in .env.local, missing in .env.production
[~] DATABASE_URL  value differs between targets
[=] DEBUG         in sync across all targets
```

---

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

---

## License

[MIT](LICENSE)