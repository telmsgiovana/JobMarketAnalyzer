import requests
from pprint import pprint

url = "https://api.lever.co/v0/postings/jobgether?mode=json"

response = requests.get(url)

jobs = response.json()

job = jobs[0]
pprint(jobs[0])
