import aiohttp
import asyncio
import base64
import logging

MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds to wait before retrying after a 503 error
RECORDS_PER_PAGE = 50  # Default Jira pagination limit

logger = logging.getLogger(__name__)


class JiraAPI:
    def __init__(self, base_url, email, api_token, max_retries=MAX_RETRIES, retry_delay=RETRY_DELAY, records_per_page=RECORDS_PER_PAGE, logger=None):
        self.base_url = base_url.rstrip("/")
        self.email = email
        self.api_token = api_token
        self.MAX_RETRIES = max_retries
        self.RETRY_DELAY = retry_delay
        self.RECORDS_PER_PAGE = records_per_page
        self._logger = logger or logging.getLogger(__name__)
        if not logger:
            logging.basicConfig(level=logging.DEBUG)

    def _get_headers(self):
        auth = f"{self.email}:{self.api_token}"
        auth_encoded = base64.b64encode(auth.encode("utf-8")).decode("utf-8")
        return {
            "Authorization": f"Basic {auth_encoded}",
            "Accept": "application/json",
        }

    async def get_data(self, session, endpoint, params=None):
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
        params = params or {}
        params["maxResults"] = self.RECORDS_PER_PAGE
        attempts = 0

        while attempts < self.MAX_RETRIES:
            try:
                self._logger.info(f"Attempt {attempts + 1} of {self.MAX_RETRIES} to fetch data from {url}")
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 503:
                        self._logger.warning(f"503 Service Unavailable. Retrying after {self.RETRY_DELAY} seconds...")
                        await asyncio.sleep(self.RETRY_DELAY)
                    elif response.status in (400, 404):
                        self._logger.warning(f"{response.status}: The server encountered an error. Response: {await response.text()}")
                        break
                    else:
                        self._logger.error(f"Error {response.status}: {await response.text()}")
                        raise Exception(f"Server error {response.status}: {await response.text()}")
            except aiohttp.ClientError as e:
                self._logger.error(f"Network error: {e}")
                raise Exception(f"Network error while fetching Jira data: {e}")
            attempts += 1

        raise Exception(f"Failed to fetch data from Jira after {self.MAX_RETRIES} attempts.")

    async def get_related_data(self, session, issue_id, relation):
        url = f"{self.base_url}/rest/api/3/issue/{issue_id}/{relation}"
        headers = self._get_headers()
        attempts = 0

        while attempts < self.MAX_RETRIES:
            try:
                self._logger.info(f"Fetching related data ({relation}) for issue {issue_id} from {url}")
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status in (400, 404):
                        self._logger.warning(f"Error {response.status}: {await response.text()}")
                        break
                    else:
                        self._logger.error(f"Error {response.status}: {await response.text()}")
                        raise Exception(f"Server error {response.status}: {await response.text()}")
            except aiohttp.ClientError as e:
                self._logger.error(f"Network error: {e}")
                raise Exception(f"Network error while fetching Jira related data: {e}")
            attempts += 1

        raise Exception(f"Failed to fetch related data from Jira after {self.MAX_RETRIES} attempts.")


# Example usage
async def main():
    jira_api = JiraAPI(
        base_url="https://your-domain.atlassian.net",
        email="your-email@example.com",
        api_token="your-api-token"
    )
    async with aiohttp.ClientSession() as session:
        issues = await jira_api.get_data(session, "/rest/api/3/search", params={"jql": "project=TEST"})
        print(issues)


if __name__ == "__main__":
    asyncio.run(main())
