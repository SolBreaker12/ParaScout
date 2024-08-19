import requests

headers = {'X-TBA-Auth-Key': ''}


def request_event_teams(event_id):
    return requests.get(f"https://www.thebluealliance.com/api/v3/event/{event_id}/teams/keys", headers).json()

