import requests
import yaml

def obtain_bearer_token(username, password):
    auth_endpoint = 'http://10.40.46.55:5000/login'
    auth_data = {'username': username, 'password': password}
    response = requests.post(auth_endpoint, json=auth_data)
    if response.status_code == 200:
        token = response.json().get('token')
        return token
    else:
        print("Failed to obtain bearer token")
        return None

def update_secrets_yaml(token):
    secrets_path = '/config/secrets.yaml'
    
    with open(secrets_path, 'r') as file:
        secrets = yaml.safe_load(file)
    
    secrets['bearer_token'] = token
    
    with open(secrets_path, 'w') as file:
        yaml.safe_dump(secrets, file)

def main():
    username = 'USERNAME'
    password = 'PASSWORD'
    token = obtain_bearer_token(username, password)
    
    if token:
        update_secrets_yaml(token)
        print("Bearer token obtained and stored in secrets.yaml")
    else:
        print("Failed to obtain bearer token")

if __name__ == "__main__":
    main()
