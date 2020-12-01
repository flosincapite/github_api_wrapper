import os
import requests


class ApiBase:

    def __init__(
            self,
            user=os.environ.get('GITHUB_USER', None),
            api_token=os.environ.get('GITHUB_TOKEN', None)):
        self._user = user
        self._api_token = api_token

    def _auth(self):
        return (self._user, self._api_token)

    def _headers(self):
        return {'Accept': 'application/vnd.github.inertia-preview+json'}


class OrgsApi(ApiBase):

    def get_id(self, organization_name, team_name):
        response = requests.get(
            f'https://api.github.com/orgs/{organization_name}/teams',
            auth=self._auth(),
            headers=self._headers())
        response_dict = response.json()
        for team in response_dict:
            if team.get('name') == team_name:
                return team.get('id')
        raise Exception(f'ID not found for team {team_name}.')


class TeamsApi(ApiBase):

    def add_permission_to_repository(self, team_id, organization, repository_name, permission):
        response = requests.put(
            f'https://api.github.com/teams/{team_id}/repos/{organization}/'
            f'{repository_name}',
            json={'permission': permission},
            auth=self._auth(),
            headers=self._headers())


class ColumnsApi(ApiBase):

    def get_id(self, project_id, column_name):
        response = requests.get(
            f'https://api.github.com/projects/{project_id}/columns',
            auth=self._auth(),
            headers=self._headers())
        response_dict = response.json()
        for column in response_dict:
            if column.get('name') == column_name:
                return column.get('id')
        raise Exception(f'ID not found for column {column_name}.')


class CardsApi(ApiBase):

    def add_card_for_issue(self, column_id, organization, repository, issue):
        response = requests.post(
            f'https://api.github.com/projects/columns/{column_id}/cards',
            json={'note': f'{organization}/{repository}/issues/{issue}'},
            auth=self._auth(),
            headers=self._headers())


class ProjectsApi(ApiBase):

    def __init__(self, *args, **kwargs):
        super(ProjectsApi, self).__init__(*args, **kwargs)
        self._columns = ColumnsApi(*args, **kwargs)
        self._cards = CardsApi(*args, **kwargs)

    def get_id(self, organization, repository, project_name):
        response = requests.get(
            (
                f'https://api.github.com/repos/{organization}/{repository}/'
                'projects'),
            auth=self._auth(),
            headers=self._headers())
        response_dict = response.json()
        print(response_dict)
        for project in response_dict:
            if project.get('name') == project_name:
                return project.get('id')
        raise Exception(f'ID not found for project {project_name}.')


class ProjectsComponent:

    def __init__(
            self,
            user=os.environ.get('GITHUB_USER', None),
            token=os.environ.get('GITHUB_TOKEN', None)):
        self._projects = ProjectsApi(user, token)
        self._columns = ColumnsApi(user, token)
        self._cards = CardsApi(user, token)
        self._orgs = OrgsApi(user, token)
        self._teams = TeamsApi(user, token)

    def add_card_from_issue(
            self,
            organization,
            repository,
            project_name,
            column_name,
            upstream_organization,
            issue_number,
            upstream_repository=None):
        project_id = self._projects.get_id(
                organization, repository, project_name)
        column_id = self._columns.get_id(project_id, column_name)
        self._cards.add_card_for_issue(
                column_id, upstream_organization,
                upstream_repository or repository, issue_number)

    def add_team_to_repository(
            self,
            organization,
            repository,
            team_name):
        team_id = self._orgs.get_id(organization, team_name)
        self._teams.add_permission_to_repository(
                team_id, organization, repository, "push")
        


if __name__ == '__main__':
    import fire
    fire.Fire(ProjectsComponent)
