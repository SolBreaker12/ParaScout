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
    auto_start_position = db.Column(db.String, nullable=False)
    auto_successful = db.Column(db.Boolean, nullable=False)  # Renamed field
    auto_target_pieces = db.Column(db.Integer, nullable=False)  # New field
    endgame = db.Column(db.String, nullable=False)  # New field
    driver_ability = db.Column(db.Integer, nullable=False)  # New field


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
    auto_start_position = request.form['auto_start_position']
    auto_successful = request.form['auto_successful'] == 'true'
    auto_target_pieces = request.form['auto_target_pieces']
    endgame = request.form['endgame']
    driver_ability = request.form['driver_ability']

    match_id = f"{match_type}{match_number}"

    match = Matches(
        team_id=team_id,
        event_id=event_id,
        match_id=match_id,
        teleop_pieces=teleop_pieces,
        auto_pieces=auto_pieces,
        defense=defense,
        auto_start_position=auto_start_position,
        auto_successful=auto_successful,
        auto_target_pieces=auto_target_pieces,
        endgame=endgame,
        driver_ability=driver_ability
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

    team_stats = []
    for team in teams:
        matches = Matches.query.filter_by(event_id=event_id, team_id=team.team_id).all()
        average_auto_points = calculate_average_auto_points(matches)
        average_teleop_points = calculate_average_teleop_points(matches)
        team_stats.append({
            'team': team,
            'average_auto_points': average_auto_points,
            'average_teleop_points': average_teleop_points
        })

    return render_template('view/events/event.html', event=event, team_stats=team_stats)


@app.route('/view/events/<event_id>/<team_id>')
def view_event_team(event_id, team_id):
    matches = Matches.query.filter_by(event_id=event_id, team_id=team_id).all()
    team = Teams.query.filter_by(team_id=team_id).first()
    event = Events.query.filter_by(event_id=event_id).first()
    preferred_auto_start_position = find_preferred_starting_position(matches)
    average_auto_points = calculate_average_auto_points(matches)
    average_teleop_points = calculate_average_teleop_points(matches)
    return render_template(
        'view/events/team.html',
        matches=matches, team=team, event=event,
        preferred_auto_start_position=preferred_auto_start_position,
        average_auto_points=average_auto_points,
        average_teleop_points=average_teleop_points)


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


def find_preferred_starting_position(matches):
    if not matches:
        return 0

    position_count = {}

    for match in matches:
        position = match.auto_start_position
        if position in position_count:
            position_count[position] += 1
        else:
            position_count[position] = 1

    preferred_position = max(position_count, key=position_count.get)
    return preferred_position


def calculate_average_auto_points(matches):
    if not matches:
        return 0

    total_auto_points = sum(match.auto_pieces for match in matches)
    average_auto_points = total_auto_points / len(matches) if matches else 0
    return average_auto_points


def calculate_average_teleop_points(matches):
    if not matches:
        return 0

    total_teleop_points = sum(match.teleop_pieces for match in matches)
    average_teleop_points = total_teleop_points / len(matches) if matches else 0
    return average_teleop_points


with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
