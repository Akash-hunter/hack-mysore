class GitHubService:
    @staticmethod
    def connect_github(student_id, auth_code):
        # TODO: Exchange auth_code for access_token, save to ExternalConnection
        pass

    @staticmethod
    def fetch_repositories(access_token):
        # TODO: Call GitHub API to get repos
        pass

    @staticmethod
    def fetch_languages(access_token, repo_name):
        # TODO: Call GitHub API to get languages for a repo
        pass

    @staticmethod
    def sync_github_data(student_id):
        # 1. Fetch connection from db
        # 2. Fetch repos & languages
        # 3. Call Evidence Engine to store/process
        pass