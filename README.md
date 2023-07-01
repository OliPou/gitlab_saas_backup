# Gitlab Saas Backup
Gitlab SaaS Backup is python script made to export single project or all projects in a gitlab group.


## Requirements

### Python
This has been made on Linux OS and MacOS.
The python script needs python 3 and the following library:

- json
- python-gitlab
- pyyaml
- requests
- pytz
- pyfiglet

### Gitlab Access

To backup your project you'll need to create a token or a user with the following right:

- At least a Maintener role
- api : Grants complete read/write access to the API, including all groups and projects, the container registry, and the package registry.

## Installation/Usage

You can use the scripts with python pipenv:

```sh
pip install pipenv
pipenv run python3 gitlab_saas_backup.py -h
usage: PROG [-h] [-t PRIVATE_TOKEN] {list_projects,backup_project,backup_group,restore_project} ...

positional arguments:
  {list_projects,backup_project,backup_group,restore_project}
                        Backup Gitlab Saas Projects
    list_projects       list all projects in a group
    backup_project      backup project by id
    backup_group        backup group by full_path access
    restore_project     restore project

optional arguments:
  -h, --help            show this help message and exit
  -t PRIVATE_TOKEN, --private-token PRIVATE_TOKEN
```

You can also use env variable for your token:

```sh
export GITLAB_TOKEN="glpat-Your-Token"
```

## Arguement list

| Mode | Argument | description | Mandatory |
|----------|-------------|---------|---------|
| `list_projects` | `-g`, `--group-path` | Full path of the group ex:namespace/my_group | `Yes` |
| `backup_project` | `-i`, `--project_id` | The id of the project to backup | `Yes` |
| `backup_project` | `-p`, `--full-path` | Full past of the file ex:/opt/backup/my_app | `Yes` |
| `backup_group` | `-g`, `--group-path` | The group full_path to backup | `Yes` |
| `backup_group` | `-d`, `--backup-directory` | Backup directory destination ex:/opt/backup/ | `Yes` |
| `backup_group` | `-r`, `--retention-days` | Specify the number of days to retain backup files | `No` |
| `restore_project` | `-n`, `--project-name-to-restore` | Name of the restored project | `Yes` |
| `restore_project` | `-p`, `--full-path` | Where your backup file is located ex:/backup/myfile | `Yes` |
| `restore_project` | `-g`, `--group-path-to-import` | Path where your want to restore your backup ex: namespace/group | `Yes` |
