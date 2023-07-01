#!/usr/bin/env python
import requests
import json
import os
import gitlab
import time
from argparse import ArgumentParser
from datetime import datetime, timedelta
import pytz
import sys
import re
import pyfiglet


class saas_backup_gitlab():

    def __init__(self, args):
        self.args = args
        self.api_url = "https://gitlab.com/api/graphql"
        self.gl = gitlab.Gitlab(private_token=self.args.private_token)
        paris_tz = pytz.timezone('Europe/Paris')
        self.current_time = datetime.now(paris_tz)
        self.formatted_date = self.current_time.strftime('%d-%m-%Y')

    def list_projects(self):
        query = '''
        {
        group(fullPath: "%s") {
            id
            projects {
            edges {
                node {
                name
                id
                }
            }
            }
        }
        }
        ''' % self.args.group_path
        headers = {
            "Authorization": f"Bearer {self.args.private_token}",
            "Content-Type": "application/json "
        }
        projects = {}
        data_to_send = json.dumps({"query": query})
        response = requests.post(self.api_url, headers=headers, data=data_to_send)
        data = response.json()
        if data['data']['group'] is None:
            print(f"{RED}Error: Permision denied or group does not exist!{RESET}")
            sys.exit(1)
        for project in data['data']['group']['projects']['edges']:
            projects[(project['node']['id']).split('/')[-1]] = project['node']['name']
        return projects, (data['data']['group']['id']).split('/')[-1]

    def backup_project(self, dest=None, project_name=None):
        project = self.gl.projects.get(self.args.project_id)
        export = project.exports.create()
        export.refresh()
        time.sleep(1)
        if dest is None:
            if "/" in self.args.full_path:
                print("I'm in")
                directory_path, file_name = os.path.split(self.args.full_path)
                backup_path = f"{directory_path}/{self.formatted_date}_{file_name}.tgz"
            backup_path = self.args.full_path
            with open(f"{backup_path}.tgz", 'wb') as f:
                export.download(streamed=True, action=f.write)
            while export.export_status != 'finished':
                export.refresh()
            return f"{GREEN}Project {backup_path} successfully backed in up{RESET}"
        else:
            backup_path = dest
            while export.export_status != 'finished':
                export.refresh()
            with open(f"{backup_path}.tgz", 'wb') as f:
                export.download(streamed=True, action=f.write)
            return f"{GREEN}Project {project_name} successfully backed up in {backup_path}{RESET}"

    def backup_group(self):
        if not os.path.exists(self.args.backup_directory):
            print(f"{RED}Backup failed: {self.args.backup_directory} is not accesible !{RESET}")
            sys.exit(1)
        projects, group_id = self.list_projects()
        if not bool(projects):
            print(f"{YELLOW}The group is empty GitlabSaasBackup did not backup anything{RESET}")
        else:
            message = "The following projects will be backed up: {}".format(", ".join(projects.values()))
            print(message)
            projects_backed_up = []
            if self.args.backup_directory:
                save_path = self.args.backup_directory[:-1]
            else:
                save_path = self.args.backup_directory

            for project_id, project_name in projects.items():
                self.args.project_id = project_id
                dest = f"{save_path}/{self.formatted_date}_{project_name}"
                status = self.backup_project(dest, project_name)
                projects_backed_up.append(project_name)
                print(status)
            if self.args.retention is not None:
                print(f"Deletion of backup older than {self.args.retention}:")
                threshold = datetime.now() - timedelta(days=self.args.retention)
                files = os.listdir(self.args.backup_directory)
                for project in projects_backed_up:
                    pattern = pattern = fr"\d{{2}}-\d{{2}}-\d{{4}}_{re.escape(project)}\.tgz"
                    file_delete = False
                    for filename in files:
                        if re.match(pattern, filename):
                            file_date = datetime.strptime(filename[:10], "%d-%m-%Y")
                            if file_date < threshold:
                                print(f"{YELLOW}Deleted file: {filename}{RESET}")
                                file_delete = True
                    if file_delete is False:
                        print(f"{GREEN}No backup to delete {project}{RESET}")
        return "Backup successfully done"

    def restore_project(self):
        self.args.group_name = self.args.group_path
        project_to_restore, group_id = self.list_projects()
        if self.args.project_name_to_restore in project_to_restore.values():
            return "project exist"
        else:
            with open(f"{self.args.full_path}", 'rb') as f:
                output = self.gl.projects.import_project(
                    f,
                    path=self.args.project_name_to_restore,
                    name=self.args.project_name_to_restore,
                    namespace=group_id,
                    override_params={'visibility': 'private'},
                )
            id = output['id']
            return f"project {self.args.project_name_to_restore} create with id : {id}"


_gitlab_token = os.environ.get('GITLAB_TOKEN')

text = "Gitlab SAS Backup"
font = "big"
ascii_art = pyfiglet.figlet_format(text, font=font)

RESET = '\033[0m'
RED = '\033[91m'
YELLOW = '\033[93m'
GREEN = '\033[92m'

parser = ArgumentParser(prog='PROG')

if os.environ.get('GITLAB_TOKEN') is None:
    parser.add_argument('-t', '--private-token', dest='private_token',
                        type=str, required=True)
else:
    parser.add_argument('-t', '--private-token', dest='private_token',
                        type=str, default=_gitlab_token)
subparsers = parser.add_subparsers(help='Backup Gitlab Saas Projects', dest='command')
parser_list_projects = subparsers.add_parser('list_projects', help='list all projects in a group')
parser_list_projects.add_argument('-g', '--group-path', dest='group_path', type=str,
                                  required=True,
                                  help="full path of the group ex:namespace/my_group")
parser_backup_project = subparsers.add_parser('backup_project', help='backup project by id')
parser_backup_project.add_argument('-i', '--project_id', dest='project_id', type=str,
                                   required=True, help="The id of the project to backup")
parser_backup_project.add_argument('-p', '--full-path', dest='full_path', type=str,
                                   required=True, help="full past of the file ex:/opt/backup/my_app")
parser_backup_group = subparsers.add_parser('backup_group', help='backup group by full_path access')
parser_backup_group.add_argument('-g', '--group-path', dest='group_path', type=str,
                                 required=True, help="The group full_path to backup")
parser_backup_group.add_argument('-d', '--backup-directory', dest='backup_directory', type=str,
                                 required=True, help="Backup directory destination ex:/opt/backup/")
parser_backup_group.add_argument('-r', '--retention-days', dest='retention', type=int,
                                 required=False, default=None, help="Specify the number of days to retain backup files")
parser_restore_project = subparsers.add_parser('restore_project', help='restore project')
parser_restore_project.add_argument('-n', '--project-name-to-restore', help='Name of the restored project',
                                    dest='project_name_to_restore', type=str,
                                    required=True)
parser_restore_project.add_argument('-p', '--full-path', dest='full_path', type=str,
                                    required=True, help="Where your backup file is located ex:/backup/myfile")
parser_restore_project.add_argument('-g', '--group-path-to-import', dest='group_path', type=str,
                                    help='Path where your want to restore your backup ex: namespace/group',
                                    required=True)

args = parser.parse_args()
g = saas_backup_gitlab(args)

functions = {
    "list_projects": g.list_projects,
    "backup_project": g.backup_project,
    "backup_group": g.backup_group,
    "restore_project": g.restore_project
    }

if args.command in functions:
    print(ascii_art)
    print(functions[args.command]())
else:
    parser.print_help()
