import argo_workflows
from argo_workflows.api import workflow_service_api
from config import config
from lib.workflow_phase import WorkflowPhase
from argo_workflows.model.io_argoproj_workflow_v1alpha1_workflow_stop_request import IoArgoprojWorkflowV1alpha1WorkflowStopRequest
from dateutil import parser
from utils.utils import custome_response
from utils.logger import logger

class ArgoWorkflow:
    def __init__(self):
        self.argowf_api_client = argo_workflows.ApiClient(self.config_argowf())
        self.argowf_api_instance = workflow_service_api.WorkflowServiceApi(self.argowf_api_client)
        self.logger = logger(__name__)

    def config_argowf(self):
        configuration = argo_workflows.Configuration(host=config.ARGO_SERVER)
        configuration.api_key['BearerToken'] = config.ARGO_API_KEY
        configuration.api_key_prefix['BearerToken'] = config.ARGO_API_KEY_PREFIX
        configuration.verify_ssl = True
        return configuration

    def get_detail_workflow(self, workflow_namespace: str, workflow_name: str):
        return self.argowf_api_instance.get_workflow(workflow_namespace, workflow_name, _check_return_type=False)
    
    def get_parameters_workflow(self, wf_parameters):
        return {item['name']: item['value'] for item in wf_parameters}
    
    def check_same_workflow_template_and_parameters(self, current_workflow_params: dict, workflow_params: dict, params_to_ignore: list):
        for key, value in current_workflow_params.items():
            if key in params_to_ignore:
                continue
            if value != workflow_params.get(key):
                return False
        return True
    
    def get_workflow_list(self, workflow_namespace: str, workflow_template_name: str):
        return self.argowf_api_instance.list_workflows(
            namespace=workflow_namespace,
            list_options_label_selector="workflows.argoproj.io/completed!=true,workflows.argoproj.io/workflow-template={}".format(workflow_template_name),
            _check_return_type=False
        )
    
    def stop_workflow(self, workflow_namespace: str, workflow_name: str, async_req: bool):
        self.argowf_api_instance.stop_workflow(
            namespace=workflow_namespace,
            name=workflow_name,
            _check_return_type=False,
            body=IoArgoprojWorkflowV1alpha1WorkflowStopRequest(
                message="Workflow stopped: The execution has been halted to ensure atomicity of operations",
                name=workflow_name,
                namespace=workflow_namespace,
            ),
            async_req=async_req,
        )

    def get_status_workflow(self, workflow_namespace: str, workflow_name: str):
        wf = self.get_detail_workflow(workflow_namespace, workflow_name)
        wf_status = wf.status['nodes'][wf.metadata['name']]['phase']
        if wf_status == WorkflowPhase.WorkflowSucceeded:
            return "success"
        elif wf_status == WorkflowPhase.WorkflowFailed:
            return "failed"
        else:
            return str(wf_status).lower()

    def atomic_workflows(self, argowf_namespace: str, argowf_name: str, params_to_ignore: list):
        should_send_notice = True
        current_wf = self.get_detail_workflow(
            workflow_namespace=argowf_namespace,
            workflow_name=argowf_name
        )
        current_wf_parameters = self.get_parameters_workflow(current_wf.spec['arguments']['parameters'])
        argowft_name = current_wf.spec['workflowTemplateRef']['name']
        wf_list = self.get_workflow_list(
            workflow_namespace=argowf_namespace,
            workflow_template_name=argowft_name
        )
        workflow_list = wf_list.items

        if not workflow_list:
            workflow_list = []
        for workflow in workflow_list:
            if workflow['metadata']['name'] == argowf_name:
                continue

            workflow_parameters = self.get_parameters_workflow(workflow['spec']['arguments']['parameters'])

            is_same_wf_and_params = self.check_same_workflow_template_and_parameters(current_wf_parameters, workflow_parameters, params_to_ignore)

            if is_same_wf_and_params:
                if parser.parse(workflow['metadata']['creationTimestamp']) > parser.parse(current_wf.metadata['creationTimestamp']):
                    should_send_notice = False
                    continue
                else:
                    self.stop_workflow(
                        workflow_namespace=argowf_namespace,
                        workflow_name=workflow['metadata']['name'],
                        async_req=True,
                    )
        return 200, custome_response("Succeeded", "The execution of workflows has been halted to ensure the atomicity of operations"), should_send_notice
