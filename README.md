# e-education
An online platform that allows learner to access resources provided by tutors

## Setup
### Environment
- Create `.env` file with the following
```bash
SECRET_KEY='secret key'
DATABASE_URL=<database url>
DEBUG='True'
ALLOWED_HOSTS='*'
MAX_VIDEO_UPLOAD_SIZE=3857600
ALLOWED_VIDEO_EXTENSIONS = 'mp4,mkv'
```
- virtual environment
```bash
# virtual
mkvirtualenv env
workon env
```

### Database
- create database and add its url to `.env` `DATABASE_URL`, tested only on postgres
- migrate the database.
```bash
python manage.py migrate
```
- you may need to delete your database if you had migrated before.

### Create Superser
- create superuser and generate a token for testing(optional)
```bash
python manage.py createsuperuser
python manage.py drf_create_token superuser_email
```

### Run tests
- Currently all will fail, code undergoing lots of changes.
```bash
python manage.py test
```

### Run development server
```bash
python manage.py runserver
```

## Endpoints
### Signup
`http://127.0.0.1:8000/api/v1/auth/users/sign_up/`

```json
{
	"first_name":"remmy",
	"last_name":"k",
	"email":"remmy@gmail.com",
	"password":"risper@1234",
	"password_confirm":"risper@1234"
}
```

### Login 
`http://127.0.0.1:8000/api/v1/auth/token/login`

```json
{
    "email":"remmy@gmail.com",
	"password":"risper@1234"
}
```

### Fetch user details
`http://127.0.0.1:8000/api/v1/auth/users/details`
- Provide token

### Post video tutorial
`http://127.0.0.1:8000/api/v1/video_tutorials/`

```json
{
	"title":"Why Black Holes Could Delete The Universe",
	"description":"Black holes are scary things. But they also might reveal the true nature of the universe to us.",
	"video_link":"https://www.youtube.com/watch?v=yWO-cvGETRQ",
	"embed_type":"Youtube"
}
```

### Post Quiz
`http://127.0.0.1:8000/api/v1/quiz/`

```json
{
	"video_tutorial":2
	
}
```

### Get details of a specific quiz
`http://127.0.0.1:8000/api/v1/quiz/1`

```json 
{
	"video_tutorial":1
}
```

### Create multichoice questions
`http://127.0.0.1:8000/api/v1/multi-choice-questions/`

```json
{
	"quiz":1,
	"position":3,
	"content":"What is the capital city of uganda?"
}
```

### Get multichoice questions
`http://127.0.0.1:8000/api/v1/multi-choice-questions`

### Edit multichoice questions
`http://127.0.0.1:8000/api/v1/multi-choice-questions/1/`

```json
{
    "position": 5
}
```

### Create choices for multichoice questions
`http://127.0.0.1:8000/api/v1/multi-choices/`

```json
{
	"question":2,
	"choice":"kisumu",
	"position": 3,
	"answer":true
}
```

### Get multichoice choices
`http://127.0.0.1:8000/api/v1/multi-choices?question=2`

### Post freeform questions
`http://127.0.0.1:8000/api/v1/free-form-questions/`

```json
{
	"quiz":1,
	"content":"When light bends as it enters a different medium the process is known as what?",
	"answer":"refraction",
	"position":2
}
```

### Get freeform questions 
`http://127.0.0.1:8000/api/v1/free-form-questions`

### Get all questions 
`http://127.0.0.1:8000/api/v1/questions`

### Start a quiz
`http://127.0.0.1:8000/api/v1/quiz/1/start_quiz`

### Submit quiz solution
`http://127.0.0.1:8000/api/v1/quiz/1/submit_quiz/`

```json
[
	{
		"question":1,
		"answer":"refraction"
	},
	{
		"question":2,
		"answer": 1
	}
]
```

