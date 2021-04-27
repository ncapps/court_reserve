# Court Reserve Bot
This project uses [Scrapy](https://docs.scrapy.org/en/latest/index.html) to make tennis court reservations.
## Getting started

- Create required environment variables
```sh
# Create .env file in project root directory
cat << EOF > .env
ORG_ID={Organization Id}
USERNAME={Login username}
PASSWORD={Login password}
MEMBER_ID1={Member Id}
MEMBER_ID2={Member Id}
EOF
```

- Configure settings

- Execute locally
```sh
pipenv run start
```
