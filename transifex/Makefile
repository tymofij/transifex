run:
	@./manage.py runserver 0.0.0.0:8000

shell:
	@./manage.py shell

dbshell:
	@./manage.py dbshell

test:
	./manage.py test actionlog projects releases resources teams \
	autofetch charts cla datastores gtranslate locks lotte priorities \
	suggestions timeline txapps watches webhooks widgets --settings=settings_test

static:
	@./manage.py collectstatic
