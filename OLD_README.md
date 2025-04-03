# bjorn

Discord bot using discordpy framework.

## Development

Use black formatter.

```bash
docker compose --profile dev run --service-ports bot_dev
```

Add `sh` if shell is wanted.

To copy league database over ssh use `scp p@192.168.3.5:/home/p/bjorn/data/league.sqlite league.sqlite`
### Enviromental variables

In .env.secret file.

- TOKEN for discord bot
- DEV
- TEST_EXTENSION

## Deployment

`sudo docker compose up -d --build`

