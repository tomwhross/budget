# ![budget header](/repo/images/budget_header.png)
A [CS50 Project](https://cs50.harvard.edu/x/2020/project/) - A simple personal budgeting web application

Based on [CS50 Finance](https://cs50.harvard.edu/x/2020/tracks/web/finance/)

## Setup

1. Clone this repo

```
$ git clone git@github.com:tomwhross/budget.git
```

2. (Optional) Create a virtual environment using the tool of your choice and activate it

```
$ python -m venv . --copies
$ source bin/activate
```

3. Install the requirements (includes dev requirements)

```
$ pip install -r requirements.txt
```

4. Initialize the database

```
$ ipython

[0] from application import *
[1] initialize_db()
```

5. Start the development server

```
$ flask run
```

6. Browse to the development server (e.g. `http://127.0.0.1:5000/`)
7. Register a new user (Default categories will be generated for the user)
