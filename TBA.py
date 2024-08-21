import requests

headers = {'X-TBA-Auth-Key': 'vnpeIvxNLYf8NABMB55UsdnY8n6L6GY7cYnokmm8q8HAT7JTmF9H9ttzuzVs9Q1t'}


def request_event_teams(event_id):
    return requests.get(f"https://www.thebluealliance.com/api/v3/event/{event_id}/teams", headers).json()
