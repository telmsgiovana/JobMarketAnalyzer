import requests
from pprint import pprint

url = "https://boards-api.greenhouse.io/v1/boards/figma/jobs?content=true"

response = requests.get(url)

jobs = response.json()


print(type(jobs["jobs"]))
print(len(jobs["jobs"]))
pprint(jobs["jobs"][0])
print(jobs["jobs"][0].keys())