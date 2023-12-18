import requests

# response = requests.post('http://localhost:5000/find_place', json={"place_name": "Eiffel Tower"})
# print(response.status_code)
# print(response.text)

response = requests.post('http://localhost:5000/search', json={"query": "Paris"})
print(response.status_code)
print(response.text)