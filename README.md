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
COST_TYPE_ID={Cost type id}
MEMBER_ID1={Member Id}
ORG_MEMBER_ID1={Membership Id}
FIRST_NAME1={First name}
LAST_NAME1={Last name}
EMAIL1={Email}
MEMBER_ID2={Member Id}
ORG_MEMBER_ID2={Membership Id}
FIRST_NAME2={First name}
LAST_NAME2={Last name}
EOF
```

- Configure court preferences
# Copy settings file and update
```sh
cp sample_settings.json settings.json
```

- Run locally
```sh
pipenv run start
```
