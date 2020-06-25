from peewee import *

db = SqliteDatabase('event.db')


class Events(Model):
    title = CharField(null=True)
    start_time = CharField(null=True)
    is_loop = CharField(null=True)
    end_time = CharField(null=True)
    duration = CharField(null=True)
    class Meta:
        database = db


if __name__ == '__main__':
    try:
        db.connect()
        db.create_tables([Events])
        db.close()
    except Exception as e:
        print(e)