from urllib.request import urlopen, Request
import json
from config import config
from utils.utils import custome_response, is_version_string
from utils.logger import logger
import os

class Slack():
    def __init__(self):
        self.logger = logger(__name__)

    def send_noti_slack(self, payload, channel_name):
        url = os.environ.get(channel_name)
        if not url:
            raise ValueError(f"{channel_name} environment variable is not set")    

        response = urlopen(Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}))
        if response.status != 200:
            self.logger.error(response.reason)
            return response.status, custome_response("Failed", response.reason)
        return response.status, custome_response("Succeeded", "Slack message sent")

    def get_environment(self, stage, commit_branch):
        if stage.lower() == "test":
            return ""

        if commit_branch == "main":
            return "STG"
        elif is_version_string(commit_branch):
            return "PRD"
        else:
            return "DEV"

    def template_slack_body(
            self,
            stage: str,
            repo_name: str,
            workflow_status: str,
            job_url: str,
            commit_branch: str,
            commit_url: str,
            author_name: str,
            message=None,
        ):
        workflow_status = workflow_status.lower()

        emoji = ":white_check_mark:" if workflow_status == "succeeded" else ":x:"
        status = "PASSED" if workflow_status == "succeeded" else "FAILED"

        slack_msg_header = f"{emoji} <{job_url}|{stage}> workflow at repo <{commit_url}|{repo_name}> {workflow_status}"
        slack_noti_message = f"{emoji} {status} - Stage: {stage} - Repo: {repo_name}"

        commit_branch = commit_branch.replace("refs/heads/", "")
        enviroment = self.get_environment(stage, commit_branch)
        
        payload = {
            "text": slack_noti_message,
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": slack_msg_header if not message else message
                    }
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": "*Branch:*\n{}".format(commit_branch)
                        },
                        {
                            "type": "mrkdwn",
                            "text": "*Author:*\n{}".format(author_name)
                        },
                    ]
                },
                {
                    "type": "divider"
                }
            ]
        }

        if enviroment:
            payload['blocks'][2]['fields'].append({
                "type": "mrkdwn",
                "text": "*Environment:*\n{}".format(enviroment)
            })

        return payload
