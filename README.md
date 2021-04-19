# tennis-bot

## Getting started

- Define environment variables
```sh
# Create .env file in project root directory
cat << EOF > .env
ORG_ID={Organization Id}
USERNAME={Login username}
PASSWORD={Login password}
EOF
```

- Execute locally
```sh
pipenv run crawl
```

## Workflow
1. Run `courtreserve` spider. Secrets are shared through env var or command line arguments.
```
$ scrapy crawl court reserve
```
2. Login to app
3. Get bookings for a given day
4. Check if there is availability for a given time
5. If availability found, create reservation

## Backlog
- Write court scheduler
- Rotate user agent
- Use download delays (2 or higher)
- Create abstract class and move courtreserve specific logic in a separate class
