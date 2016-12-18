import click
import yaml
import json
import os.path
import time
import getpass
import github_token
from dothub.github_helper import GitHub
from dothub.repository import Repo


APP_DIR = click.get_app_dir("dothub")
CONFIG_FILE = os.path.join(APP_DIR, "config.json")
DEFAULT_API_URL = "https://api.github.com"
REPO_CONFIG_FILE = ".dothub.repo.yml"


def load_config():
    """Returns a config object loaded from disk or an empty dict"""
    try:
        with open(CONFIG_FILE) as f:
            conf = json.load(f)
    except IOError:
        conf = dict()
        conf["metadata"] = dict(config_time=time.time())
        if not os.path.isdir(APP_DIR):
            os.mkdir(APP_DIR)
        click.echo("Seems this is the first time you run dothub, let me configure your settings...")
        initial_config(conf)
        with open(CONFIG_FILE, 'w') as f:
            conf = json.dump(conf, f)
        click.echo("Config saved in: '{}'".format(CONFIG_FILE))
        click.echo("Delete this file to rerun the wizard")
    return conf


def initial_config(conf):
    """Asks the user for the general configuration for the app and fills the config object"""
    user = click.prompt("What is your username? ")
    password = getpass.getpass()
    token_factory = github_token.TokenFactory(user, password, "gitorg", github_token.ALL_SCOPES)
    token = token_factory(tfa_token_callback=lambda: click.prompt("Insert your TFA token: "))
    conf["token"] = token
    github_url = click.prompt("What is your github instance API url? ", default=DEFAULT_API_URL)
    conf["github_base_url"] = github_url


@click.group()
@click.option("--user", help="GitHub user to use", envvar="GITHUB_USER", required=True)
@click.option("--token", help="GitHub API token to use", envvar="GITHUB_TOKEN", required=True)
@click.option("--github_base_url", help="GitHub base api url",
              envvar="GITHUB_API_URL", default=DEFAULT_API_URL)
@click.pass_context
def dothub(ctx, user, token, github_base_url):
    """Configure github as code!

    Stop using the keyboard like a mere human and store your github config in a file"""
    gh = GitHub(user, token, github_base_url)
    ctx.obj['github'] = gh


@dothub.command()
@click.option("--organization", help="GitHub organization of the repo", required=True)
@click.option("--repository", help="GitHub repo to serialize", required=True)
@click.option("--config_file", help="Output config file", default=REPO_CONFIG_FILE)
@click.pass_context
def repo(ctx, organization, repository, config_file):
    """Retrieve the repository config locally"""
    gh = ctx.obj['github']
    r = Repo(gh, organization, repository)
    repo_config = r.describe()
    with open(config_file, 'w') as f:
        yaml.safe_dump(repo_config, f, encoding='utf-8', allow_unicode=True, default_flow_style=False)