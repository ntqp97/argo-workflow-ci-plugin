import os

class Config(object):

    GIT_PROVIDER = os.environ.get('GIT_PROVIDER')
    GIT_SERVER = os.environ.get('GIT_SERVER')
    TARGET_PIPELINE_URL = os.environ.get('TARGET_URL')
    GIT_ACCESS_TOKEN = os.environ.get('GIT_ACCESS_TOKEN')

    URL = os.environ.get('URL')

    ARGO_API_KEY = os.environ.get('ARGO_API_KEY')
    ARGO_API_KEY_PREFIX = os.environ.get('ARGO_API_KEY_PREFIX', 'Bearer')
    ARGO_SERVER = os.environ.get('ARGO_SERVER')

config = Config()
