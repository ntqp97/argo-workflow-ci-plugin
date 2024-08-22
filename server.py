import json
import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
from http import HTTPStatus
from lib.slack import Slack
from lib.git import GitLab, Repo
from lib.argo_workflow import ArgoWorkflow
import contextlib
from utils.utils import get_value, custome_response
from config import config
from utils.logger import logger

class PluginHandler(BaseHTTPRequestHandler):
    def __init__(self, request, client_address, server) -> None:
        self.logger = logger(__name__)
        super().__init__(request, client_address, server)

    def args(self):
        return json.loads(self.rfile.read(int(self.headers.get('Content-Length'))))

    def reply(self, code, reply):
        self.send_response(code)
        self.end_headers()
        self.wfile.write(json.dumps(reply).encode("UTF-8"))

    def forbidden(self):
        self.send_response(403)
        self.end_headers()
    
    def badrequest(self, error):
        self.send_response(code=HTTPStatus.BAD_REQUEST, message=error)
        self.end_headers()

    def unsupported(self):
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        content_type = self.headers['Content-Type']
        if content_type != 'application/json':
            self.badrequest("Content-Type header is not set to 'application/json'")

        if self.path == '/api/v1/template.execute':
            args = self.args()
            argowf_client = ArgoWorkflow()
            argowf_name = args['workflow']['metadata']['name']
            argowf_namespace = args['workflow']['metadata']['namespace']
            should_send_notice = True
            try:
                if 'argo-workflow-executor-plugin' in args['template'].get('plugin', {}):
                    target_address = f"{config.ARGO_SERVER}/workflows/{argowf_namespace}/{argowf_name}"
                    if 'argo-workflow-atomic-executor-plugin' in args['template']['plugin']['argo-workflow-executor-plugin']:
                        self.logger.info(f"Processing argo-workflow-atomic-executor-plugin")

                        args_argo_workflow_atomic_executor_plugin = args['template']['plugin']['argo-workflow-executor-plugin']['argo-workflow-atomic-executor-plugin']
                        params_to_ignore = args_argo_workflow_atomic_executor_plugin.get(
                            'params_to_ignore', 'last_commit_message,checkout_sha,commit_url').split(',')

                        _, _, should_send_notice = argowf_client.atomic_workflows(
                            argowf_namespace=argowf_namespace,
                            argowf_name=argowf_name,
                            params_to_ignore=params_to_ignore,
                        )
                    if 'slack-executor-plugin' in args['template']['plugin']['argo-workflow-executor-plugin'] and should_send_notice:
                        self.logger.info(f"Processing slack-executor-plugin")
                        args_slack_executor_plugin = args['template']['plugin']['argo-workflow-executor-plugin']['slack-executor-plugin']
                        slack = Slack()
                        if args_slack_executor_plugin['config'].get('use_template'):
                            payload = slack.template_slack_body(
                                stage=args_slack_executor_plugin.get('stage'),
                                repo_name=args_slack_executor_plugin.get('repo_name'),
                                workflow_status=args_slack_executor_plugin.get('workflow_status'),
                                job_url=target_address,
                                commit_branch=args_slack_executor_plugin.get('commit_branch'),
                                commit_url=args_slack_executor_plugin.get('commit_url'),
                                author_name=args_slack_executor_plugin.get('author_name'),
                                message=args_slack_executor_plugin.get('message'),
                            )
                        else:
                            text = args_slack_executor_plugin.get('text')
                            blocks = args_slack_executor_plugin.get('blocks')
                            payload = {
                                'text': text,
                                'blocks': blocks
                            }
                        self.logger.info(f"payload: {payload}")
                        slack.send_noti_slack(payload, args_slack_executor_plugin['config'].get('channel', 'URL'))

                    if 'git-executor-plugin' in args['template']['plugin']['argo-workflow-executor-plugin'] and should_send_notice:
                        self.logger.info(f"Processing git-executor-plugin")
                        args_git_executor_plugin = args['template']['plugin']['argo-workflow-executor-plugin']['git-executor-plugin']

                        repo = Repo(
                            owner=get_value(args_git_executor_plugin, 'owner'),
                            repo=get_value(args_git_executor_plugin, 'repo'),
                            pr_number=get_value(args_git_executor_plugin, 'pr_number'),
                            username=get_value(args_git_executor_plugin, 'username'),
                            status=get_value(args_git_executor_plugin, 'status'),
                            target=target_address,
                            label=get_value(args_git_executor_plugin, 'label'),
                            commit_sha=get_value(args_git_executor_plugin, 'commit_sha'),
                            project_id=get_value(args_git_executor_plugin, 'project_id'),
                            commit_branch=get_value(args_git_executor_plugin, 'commit_branch'),
                        )

                        if (not repo.status):
                            status = argowf_client.get_status_workflow(
                                workflow_namespace=argowf_namespace,
                                workflow_name=argowf_name
                            )
                            repo.status = status

                        gitlab_client = GitLab(repo=repo)
                        gitlab_client.create_status()
                    self.logger.info("Plugin execute successfully")
                    self.reply(200, custome_response("Succeeded", "Plugin execute successfully"))
                else:
                    self.reply({})
            except Exception as e:
                self.logger.error(str(e))
                self.reply(400, custome_response("Failed", str(e)))
        else:
            self.unsupported()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="HTTP Server for Argo Workflow Executor")
    parser.add_argument("--port", default=7522, type=int, help="The port of the HTTP server")
    args = parser.parse_args()

    with contextlib.suppress(Exception):
        httpd = HTTPServer(("", args.port), PluginHandler)
        print("Starting HTTP server...")
        httpd.serve_forever()
