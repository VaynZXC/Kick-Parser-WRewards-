import requests

response = requests.get('http://94.241.142.146:5000/')
print(response.text)