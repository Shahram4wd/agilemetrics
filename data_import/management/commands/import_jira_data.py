import logging
import os
import aiohttp
import asyncio
from asgiref.sync import sync_to_async
from django.core.management.base import BaseCommand
from data_import.jira_api import JiraAPI  # Adjusted import
from data_import.data_processor import DataProcessor
from data_import.registry import ProcessorRegistry
from datetime import datetime as DateTime
from typing import Optional, Dict, Any, List
import random

logger = logging.getLogger(__name__)
BATCH_SIZE = 50  # Default maxResults for Jira API
INITIAL_CONCURRENT_FETCHES = 3
MIN_CONCURRENT_FETCHES = 1
MAX_RETRY_DELAY = 30
INITIAL_RETRY_DELAY = 10
MAX_RETRIES = 5


class Command(BaseCommand):
    help = 'Imports data from Jira API and processes it sequentially for each endpoint.'

    def __init__(self, logger: Optional[logging.Logger] = None):
        super().__init__()
        self._logger = logger or logging.getLogger(__name__)
        if not logger:
            logging.basicConfig(level=logging.DEBUG)
        self.registry = ProcessorRegistry.get_instance()
        self.current_concurrent_fetches = INITIAL_CONCURRENT_FETCHES

    def add_arguments(self, parser):
        parser.add_argument(
            '--endpoint', 
            type=str, 
            choices=list(self.registry.endpoints.keys()),  
            help='Specify which endpoint to fetch data from. Leave empty to fetch all.'
        )
        parser.add_argument(
            '--max-concurrent',
            type=int,
            default=INITIAL_CONCURRENT_FETCHES,
            help=f'Maximum number of concurrent page fetches (default: {INITIAL_CONCURRENT_FETCHES})'
        )

    async def get_latest_update(self, endpoint: str) -> DateTime:
        """Fetch the latest update timestamp for incremental sync."""
        model_class = self.registry.models[endpoint]
        latest_update = await sync_to_async(
            model_class.objects.order_by('-last_update').values_list('last_update', flat=True).first
        )()
        return latest_update if latest_update else DateTime(1970, 1, 1)

    def handle(self, *args: Any, **options: Dict[str, Any]):
        logging.basicConfig(level=logging.INFO)
        endpoint = options.get('endpoint')
        max_concurrent = options.get('max_concurrent', INITIAL_CONCURRENT_FETCHES)
        asyncio.run(self.async_handle(endpoint, max_concurrent))

    async def async_handle(self, endpoint: Optional[str] = None, max_concurrent: int = INITIAL_CONCURRENT_FETCHES):
        if endpoint:
            await self.process_endpoint(endpoint, max_concurrent)
        else:
            for ep in self.registry.endpoints.keys():
                self._logger.info(f"Starting processing for endpoint: {ep}")
                await self.process_endpoint(ep, max_concurrent)
                self._logger.info(f"Completed processing for endpoint: {ep}")

    async def process_endpoint(self, endpoint: str, max_concurrent: int):
        start_time = DateTime.now()

        credentials = {
            'base_url': os.getenv('JIRA_BASE_URL'),
            'email': os.getenv('JIRA_USER'),
            'api_token': os.getenv('JIRA_API_TOKEN'),
        }

        if not all(credentials.values()):
            self._logger.error("Missing required Jira API credentials")
            return

        url = self.registry.endpoints[endpoint]
        latest_update = await self.get_latest_update(endpoint)

        self._logger.info(f"Started fetching {endpoint} from Jira API (after {latest_update})")

        jira_api = JiraAPI(
            base_url=credentials['base_url'],
            email=credentials['email'],
            api_token=credentials['api_token'],
            max_retries=MAX_RETRIES,
            retry_delay=MAX_RETRY_DELAY,
            records_per_page=BATCH_SIZE,
            logger=self._logger
        )
        data_processor = DataProcessor(self._logger)
        processor_class = self.registry.processors[endpoint]
        processor = processor_class(self._logger, data_processor)

        async with aiohttp.ClientSession() as session:
            try:
                total_processed = await self.fetch_and_process_paginated_data(
                    session=session,
                    jira_api=jira_api,
                    processor=processor,
                    endpoint=endpoint,
                    url=url,
                    latest_update=latest_update,
                    max_concurrent=max_concurrent
                )
                duration = DateTime.now() - start_time
                self._logger.info(
                    f"Finished processing {endpoint}. "
                    f"Total records: {total_processed}. Duration: {duration}."
                )
            except Exception as e:
                self._logger.error(f"Error processing {endpoint}: {str(e)}", exc_info=True)

    async def fetch_with_retry(self, session, jira_api, url, params, max_retries=5):
        """Fetch a single page with exponential backoff retry."""
        retry_delay = INITIAL_RETRY_DELAY
        attempt = 1

        while attempt <= max_retries:
            try:
                self._logger.debug(f"Fetching page: {url}, params {params}, attempt {attempt}")
                data = await jira_api.get_data(session, url, params=params)
                return data
            except aiohttp.ClientResponseError as e:
                if e.status == 503:
                    if attempt < max_retries:
                        jitter = random.uniform(0.5, 1.5)
                        delay = min(retry_delay * jitter, MAX_RETRY_DELAY)
                        self._logger.warning(
                            f"503 Service Unavailable. Retrying after {delay:.1f} seconds... "
                            f"(attempt {attempt}/{max_retries})"
                        )
                        await asyncio.sleep(delay)
                        retry_delay *= 2
                        attempt += 1
                        continue
                raise
            except Exception as e:
                self._logger.error(f"Error fetching page: {str(e)}")
                raise

    async def fetch_and_process_paginated_data(self, session, jira_api, processor, 
                                             endpoint, url, latest_update, max_concurrent):
        """Fetch and process paginated data with dynamic concurrency adjustment."""
        start_at = 0
        total_records_processed = 0
        self.current_concurrent_fetches = max_concurrent

        while True:
            params = {
                "startAt": start_at,
                "maxResults": BATCH_SIZE,
                "updated": latest_update.isoformat() if latest_update else None,
            }
            try:
                result = await self.fetch_with_retry(session, jira_api, url, params)
                if not result or not result.get('issues'):
                    return total_records_processed
                
                num_records = await processor.process_objects(result['issues'], BATCH_SIZE)
                total_records_processed += num_records
                self._logger.info(
                    f"Processed {num_records} records from {endpoint}. Total processed: {total_records_processed}."
                )

                if len(result['issues']) < BATCH_SIZE:
                    return total_records_processed
                
                start_at += BATCH_SIZE
            except Exception as e:
                self._logger.error(f"Error processing data: {str(e)}")
                break
