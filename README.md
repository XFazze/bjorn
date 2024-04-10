# bjorn

Discord bot using discordpy framework.

## Development

Use black formatter.

### Run dev bot

```bash
docker compose --profile dev run --service-ports bot_dev
```

Add `sh` if shell is wanted.

### Run tests

```bash
docker compose --profile test run --service-ports tests
```

### Enviromental variables

In .env.secret file.

Needed:

- TOKEN for discord bot
- DB for sqlite database location (/data/data.sqlite)

For developing

- PREFIX
- DEV should be true for developing
- TEST_COG which cog to load while in dev mode

### Usefull links

- <https://dpytest.readthedocs.io/en/latest/tutorials/index.html>
- <https://discordpy.readthedocs.io/en/stable/api.html>
