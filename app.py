from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
import TBA


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
    auto_pieces = db.Column(db.Integer, nullable=False)
    teleop_pieces = db.Column(db.Integer, nullable=False)
    defense = db.Column(db.Boolean, nullable=False)
    # score = db.Column(db.Integer, nullable=False)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/scout/match')
def scout_match():
    events = Events.query.all()
    return render_template('scout/match_scout.html', events=events)


@app.route('/scout/submit_match_data', methods=['POST'])
def submit_match_data():
    team_id = request.form['team_id']
    event_id = request.form['event_id']
    match_type = request.form['match_type']
    match_number = request.form['match_number']
    teleop_pieces = request.form['teleop_pieces']
    auto_pieces = request.form['auto_pieces']
    defense = 'defense' in request.form

    # Combine match_type and match_number to create match_id
    match_id = f"{match_type}{match_number}"

    # Create a new Matches entry
    match = Matches(
        team_id=team_id,
        event_id=event_id,
        match_id=match_id,
        teleop_pieces=teleop_pieces,
        auto_pieces=auto_pieces,
        defense=defense
    )

    db.session.add(match)
    db.session.commit()
    return redirect(url_for('success'))


@app.route('/scout/pit')
def scout_pit():
    return render_template('scout/pit_scout.html')


@app.route('/scout/success')
def success():
    return render_template('scout/success.html')


@app.route('/view/events')
def view_events():
    events = Events.query.all()
    return render_template('view/events.html', events=events)


@app.route('/view/events/<event_id>')
def view_event(event_id):
    event = Events.query.filter_by(event_id=event_id).one()
    event_teams = EventTeams.query.filter_by(event_id=event_id).all()

    team_ids = [et.team_id for et in event_teams]

    teams = Teams.query.filter(Teams.team_id.in_(team_ids)).all()

    matches = Matches.query.filter_by(event_id=event_id).all()

    return render_template('view/events/event.html', event=event, teams=teams, matches=matches)


@app.route('/view/events/<event_id>/<team_id>')
def view_event_team(event_id, team_id):
    matches = Matches.query.filter_by(event_id=event_id, team_id=team_id).all()

    return render_template('view/events/team.html', matches=matches)


@app.route('/view/matches')
def view_matches():
    matches = Matches.query.all()
    return render_template('view/matches.html', matches=matches)


@app.route('/admin')
def admin():
    events = Events.query.all()
    return render_template('admin.html', events=events)


@app.route('/admin/add_event', methods=['POST'])
def add_event():
    event_name = request.form['event_name']
    event_id = request.form['event_id']
    new_event = Events(event_id=event_id, name=event_name)
    db.session.add(new_event)
    db.session.commit()

    teams = TBA.request_event_teams(event_id)
    for team in teams:
        team_id = team["team_number"]
        existing_team = Teams.query.filter_by(team_id=team_id).first()
        if not existing_team:
            team_name = team["nickname"]
            new_team = Teams(team_id=team_id, name=team_name)
            db.session.add(new_team)

        new_event_team = EventTeams(event_id=event_id, team_id=team_id)
        db.session.add(new_event_team)

    db.session.commit()
    return redirect(url_for('admin'))


@app.route('/admin/delete_event/<string:event_id>', methods=['POST'])
def delete_event(event_id):
    event = Events.query.get_or_404(event_id)

    EventTeams.query.filter_by(event_id=event_id).delete()
    Matches.query.filter_by(event_id=event_id).delete()

    db.session.delete(event)
    db.session.commit()

    return jsonify({"success": True})


with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
