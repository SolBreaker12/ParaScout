from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
import TBA

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///scouting_data.db'
db = SQLAlchemy(app)

app.secret_key = 'admin_pass'  # Not a high-security app so no problem


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
    auto_successful = db.Column(db.Boolean, nullable=False)
    auto_target_pieces = db.Column(db.Integer, nullable=False)
    endgame = db.Column(db.String, nullable=False)
    driver_ability = db.Column(db.Integer, nullable=False)


class PitScouting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.team_id'), nullable=False)
    event_id = db.Column(db.String, db.ForeignKey('events.event_id'), nullable=False)
    drivetrain_type = db.Column(db.String(50), nullable=False)
    defense_capability = db.Column(db.String(50), nullable=False)
    anti_defense_capability = db.Column(db.String(50), nullable=False)
    number_of_autos = db.Column(db.Integer, nullable=False)
    auto_consistency = db.Column(db.String(50), nullable=False)
    average_cycle_time = db.Column(db.Integer, nullable=False)
    endgame_ability = db.Column(db.String(50), nullable=False)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)

    return decorated_function


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
    events = Events.query.all()
    return render_template('scout/pit_scout.html', events=events)


@app.route('/submit_pit_scout', methods=['POST'])
def submit_pit_scout():
    team_id = request.form['team_id']
    event_id = request.form['event_id']
    drivetrain_type = request.form['drivetrain_type']
    defense_capability = request.form['defense_capability']
    anti_defense_capability = request.form['anti_defense_capability']
    number_of_autos = request.form['number_of_autos']
    auto_consistency = request.form['auto_consistency']
    average_cycle_time = request.form['average_cycle_time']
    endgame_ability = request.form['endgame_ability']

    new_pit_scout = PitScouting(
        team_id=team_id,
        event_id=event_id,
        drivetrain_type=drivetrain_type,
        defense_capability=defense_capability,
        anti_defense_capability=anti_defense_capability,
        number_of_autos=number_of_autos,
        auto_consistency=auto_consistency,
        average_cycle_time=average_cycle_time,
        endgame_ability=endgame_ability
    )

    db.session.add(new_pit_scout)
    db.session.commit()

    return redirect(url_for('success'))


@app.route('/scout/success')
def success():
    return render_template('scout/success.html')


@app.route('/view/events')
def view_events():
    events = Events.query.all()
    return render_template('view/events.html', events=events)


@app.route('/view/events/<event_id>')
def view_event(event_id):
    # Get the event row that matches URL event_id
    event = Events.query.filter_by(event_id=event_id).one()
    # Get all teams at same event
    event_teams = EventTeams.query.filter_by(event_id=event_id).all()
    # Separate all team_ids and get all teams with the same id
    team_ids = [et.team_id for et in event_teams]
    teams = Teams.query.filter(Teams.team_id.in_(team_ids)).all()

    # Calculate average auto and teleop points for each team using helper functions
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
    # Render the event page with the event and team stats
    return render_template('view/events/event.html', event=event, team_stats=team_stats)


@app.route('/view/events/<event_id>/<team_id>')
def view_event_team(event_id, team_id):
    matches = Matches.query.filter_by(event_id=event_id, team_id=team_id).all()
    team = Teams.query.filter_by(team_id=team_id).first()
    event = Events.query.filter_by(event_id=event_id).first()
    preferred_auto_start_position = find_preferred_starting_position(matches)
    average_auto_points = calculate_average_auto_points(matches)
    average_teleop_points = calculate_average_teleop_points(matches)

    pit_scouting = PitScouting.query.filter_by(event_id=event_id, team_id=team_id).first()

    return render_template(
        'view/events/team.html',
        matches=matches, team=team, event=event,
        preferred_auto_start_position=preferred_auto_start_position,
        average_auto_points=average_auto_points,
        average_teleop_points=average_teleop_points,
        pit_scouting=PitScouting.query.filter_by(event_id=event_id, team_id=team_id).first()
    )


@app.route('/view/matches')
def view_matches():
    matches = Matches.query.all()
    return render_template('view/matches.html', matches=matches)


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    error_message = None
    if request.method == 'POST':
        password = request.form['password']
        if password == app.secret_key:  # Ensure this matches the correct admin password
            session['logged_in'] = True
            return redirect(url_for('admin'))
        else:
            error_message = 'Incorrect password. Please try again.'
    return render_template('admin_login.html', error_message=error_message)


@app.route('/admin')
@login_required
def admin():
    events = Events.query.all()
    return render_template('admin.html', events=events)


@app.route('/admin/add_event', methods=['POST'])
@login_required
def add_event():
    event_name = request.form['event_name']
    event_id = request.form['event_id']
    new_event = Events(event_id=event_id, name=event_name)

    try:
        teams = TBA.request_event_teams(event_id)
        if not isinstance(teams, list):
            raise ValueError("Invalid response format from TBA.request_event_teams")
        if not teams:
            raise ValueError("Invalid event ID")
    except Exception as e:
        db.session.rollback()
        error_message = f"Failed to fetch teams for the event. Error: {str(e)}"
        return render_template('admin.html', events=Events.query.all(), error_message=error_message)

    db.session.add(new_event)
    db.session.commit()

    for team in teams:
        if not isinstance(team, dict):
            raise ValueError("Invalid team data format")
        team_id = team["team_number"]  # Ensure team is a dictionary and "team_number" is a valid key
        existing_team = Teams.query.filter_by(team_id=team_id).first()
        if not existing_team:
            team_name = team["nickname"]  # Ensure "nickname" is a valid key
            new_team = Teams(team_id=team_id, name=team_name)
            db.session.add(new_team)

        new_event_team = EventTeams(event_id=event_id, team_id=team_id)
        db.session.add(new_event_team)

    db.session.commit()
    return redirect(url_for('admin'))


@app.route('/admin/delete_event/<string:event_id>', methods=['POST'])
@login_required
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
    # Sum of all pieces
    total_auto_points = sum(match.auto_pieces for match in matches)
    # Average of all pieces
    average_auto_points = total_auto_points / len(matches) if matches else 0
    return average_auto_points


# Same as previous, just for teleop pieces
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
