from flask import Flask, render_template

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/scout/game')
def game():
    return render_template('scout/match_data.html')


@app.route('/scout/pit')
def pit():
    return render_template('scout/pit_data.html')


@app.route('/view')
def view():
    return render_template('view.html')


@app.route('/event/<event_id>')
def event(event_id):
    return render_template('event/event.html', event_id=event_id)


@app.route('/event/<event_id>/<match_id>')
def event_match(event_id, match_id):
    return render_template('event/match.html', event_id=event_id, match_id=match_id)


if __name__ == '__main__':
    app.run(debug=True)
