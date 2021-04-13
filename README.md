# tennis-bot

## Getting started
```sh
$ scrapy crawl courtreserve
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
