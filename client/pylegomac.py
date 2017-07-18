import os
import click
import requests
import yaml


def get_config(filename):
    with open(filename) as f:
        config = yaml.load(f)
    return config


def save_config(filename, config):
    with open(filename, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)


def get_token(url, username):
    password = click.prompt('Password', hide_input=True)
    payload = {'username': username, 'password': password}
    r = requests.post(url + '/login', json=payload)
    r.raise_for_status()
    return r.json()['token']


def send_message(url, token, message):
    payload = {'message': message}
    headers = {'Authorization': token}
    r = requests.post(url + '/messages', json=payload, headers=headers)
    r.raise_for_status()


@click.command()
@click.option('--conf', '-c', default='~/.pylegomac.yml',
              help='Configuration file [default: "~/.pylegomac.yml"]')
@click.argument('message')
@click.version_option()
def pylegomac(message, conf):
    """Send message to aiolegomac server"""
    filename = os.path.expanduser(conf)
    config = get_config(filename)
    url = config['url']
    username = config['username']
    if 'token' in config:
        try:
            send_message(url, config['token'], message)
        except requests.exceptions.HTTPError as err:
            # Token no more valid
            pass
        else:
            click.echo('Message sent')
            return
    token = get_token(url, username)
    send_message(url, token, message)
    config['token'] = token
    save_config(filename, config)


if __name__ == '__main__':
    pylegomac()
