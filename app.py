from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///scouting_data.db'
db = SQLAlchemy(app)


class Teams(db.Model):
    team_id = db.Column(db.Integer, primary_key=True, unique=True, nullable=False)
    name = db.Column(db.String, nullable=False)


class Events(db.Model):
    event_id = db.Column(db.String, primary_key=True, unique=True, nullable=False)
    name = db.Column(db.String, nullable=False)


class EventTeams(db.Model):
    event_team_id = db.Column(db.Integer, primary_key=True, unique=True, nullable=False, autoincrement=True)
    event_id = db.Column(db.String, db.ForeignKey('events.event_id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.team_id'), nullable=False)


class Matches(db.Model):
    id = db.Column(db.Integer, primary_key=True, unique=True, nullable=False, autoincrement=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.team_id'), nullable=False)
    event_id = db.Column(db.String, db.ForeignKey('events.event_id'), nullable=False)
    match_id = db.Column(db.String, nullable=False)
    score = db.Column(db.Integer, nullable=False)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/scout/match')
def scout_match():
    return render_template('scout/match_scout.html')


@app.route('/scout/submit_match_data', methods=['POST'])
def submit_match_data():
    match = Matches(
        team_id=request.form['team_id'],
        event_id=request.form['event_id'],
        match_id=request.form['match_id'],
        score=request.form['score']
    )

    db.session.add(match)
    db.session.commit()
    return redirect(url_for('success'))


@app.route('/scout/pit')
def scout_pit():
    return render_template('scout/pit_scout.html')


@app.route('/success')
def success():
    return render_template('scout/success.html')


@app.route('/view')
def view():
    return render_template('view.html')


@app.route('/view/events')
def view_events():
    events = Events.query.all()
    return render_template('view/events.html', events=events)


@app.route('/view/events/<event_id>')
def view_event_teams(event_id):
    event = Events.query.filter_by(event_id=event_id).one()
    event_teams = EventTeams.query.filter_by(event_id=event_id).all()
    return render_template('view/events/event.html', event=event, event_teams=event_teams)


@app.route('/view/matches')
def view_matches():
    matches = Matches.query.all()
    return render_template('view/matches.html', matches=matches)


with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
