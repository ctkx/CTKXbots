FROM python:3

RUN pip3 install nextcord \
                 mysql.connector \
                 tabulate \
                 gspread \
                 gspread_formatting

CMD [ "python","-u","/bot/bot.py" ]
