import gitlab
from config import config
from utils.utils import custome_response, get_branch_name
from utils.logger import logger

class Repo:
    def __init__(self, owner, repo, pr_number, username, status, target, label, commit_sha, project_id, commit_branch):
        self.provider = config.GIT_PROVIDER
        self.server = config.GIT_SERVER
        self.owner = owner
        self.repo = repo
        self.pr_number = pr_number
        self.username = username
        self.token = config.GIT_ACCESS_TOKEN
        self.status = status
        self.target = target
        self.label = label
        self.commit_sha = commit_sha
        self.project_id = project_id
        self.commit_branch = commit_branch

    def get_repo_path(self):
        return "{}/{}".format(self.owner, self.repo)

class GitLab:
    def __init__(self, repo: Repo):
        self.repo = repo
        self.git_client = gitlab.Gitlab(url=repo.server, private_token=repo.token)
        self.logger = logger(__name__)
    
    def create_status(self):
        project = self.git_client.projects.get(self.repo.project_id)
        commit = project.commits.get(self.repo.commit_sha)
        self.logger.info(f'state: {self.repo.status} - name: {self.repo.label} - target_url: {self.repo.target}')
        res = commit.statuses.create({
            'ref': get_branch_name(self.repo.commit_branch),
            'state': self.repo.status,
            'name': self.repo.label,
            'target_url': self.repo.target
        })
        return 200, custome_response("Succeeded", res.pformat())
