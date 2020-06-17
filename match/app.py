from flask import Flask
import src.schedule as sch

app = Flask(__name__)


@app.route('/api/schedule')
def home():
    sch.run()


if __name__ == '__main__':
    sch.run()
