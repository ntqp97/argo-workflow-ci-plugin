class WorkflowPhase:
    WorkflowUnknown = ""
    WorkflowPending = "Pending"
    WorkflowRunning = "Running"
    WorkflowSucceeded = "Succeeded"
    WorkflowFailed = "Failed"
    WorkflowError = "Error"

    @staticmethod
    def completed(phase):
        return phase in [WorkflowPhase.WorkflowSucceeded, WorkflowPhase.WorkflowFailed, WorkflowPhase.WorkflowError]
