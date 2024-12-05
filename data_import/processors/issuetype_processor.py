from data_import.models import IssueType
from data_import.base_processor import BaseProcessor, FieldMapping
from data_import.registry import ProcessorRegistry
import os


def register_processor(registry: ProcessorRegistry):
    registry.register(
        endpoint='issuetypes',
        api_url=os.getenv('JIRA_SERVER')+'rest/api/3/issuetype/issuetype',
        model=IssueType,
        processor_class=IssueTypeProcessor
    )


class IssueTypeProcessor(BaseProcessor):
    field_mappings = {
        'id': FieldMapping('id', 'id', 'string', required=True, is_primary_key=True),
        'name': FieldMapping('name', 'name', 'string'),
        'description': FieldMapping('description', 'description', 'string'),
        'icon_url': FieldMapping('iconUrl', 'icon_url', 'string'),
        'hierarchy_level': FieldMapping('hierarchyLevel', 'hierarchy_level', 'int'),
        'avatar_id': FieldMapping('avatarId', 'avatar_id', 'int'),
        'subtask': FieldMapping('subtask', 'subtask', 'boolean'),
        'project_scope': FieldMapping('scope', 'project_scope', 'json')
    }

    async def process_objects(self, json_data: str, batch_size: int) -> int:
        """Process issue type objects using the shared logic in BaseProcessor."""
        entries = self.data_processor.parse_json(json_data)
        return await self.process_entries(entries, IssueType, self.field_mappings, batch_size)
