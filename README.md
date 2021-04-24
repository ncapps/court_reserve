# Court Reserve Bot
A tiny python project that schedules tennis court reservations.
## Getting started

- Define environment variables
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

- Execute locally
```sh
pipenv run start
```
