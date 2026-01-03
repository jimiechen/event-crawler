import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class Tag(BaseModel):
    type: str  # 'date', 'volume', 'block', 'concept', 'industry', 'other'
    value: str
    raw: str
    description: str = ""
    is_dynamic: bool = False

class TagService:
    # Predefined patterns
    # Matches "2.9倍", "2.9倍量", "2.9倍以上"
    VOLUME_PATTERN = re.compile(r'(\d+(?:\.\d+)?)倍(?:量|以上)?')
    DATE_PATTERN_CN = re.compile(r'(\d{4})年(\d{1,2})月(\d{1,2})日')
    DATE_PATTERN_ISO = re.compile(r'(\d{4})-(\d{2})-(\d{2})')
    
    BLOCK_TAGS = sorted(['非创业版', '非科创版', '非ST', 'ST', '创业版', '科创版'], key=len, reverse=True)
    
    @classmethod
    def parse_query(cls, query: str) -> Dict[str, Any]:
        """
        Parse a natural language query into structured tags.
        """
        tags = []
        if not query:
            return {'tags': [], 'structure': {}}

        # Normalize separators
        query_parts = query.replace('，', ' ').replace(',', ' ').split()
        
        parsed_structure = {
            'volume': [],
            'date': [],
            'block': [],
            'concept': [],
            'other': []
        }
        
        for part in query_parts:
            part = part.strip()
            if not part:
                continue
                
            matched = False
            
            # Volume
            vol_match = cls.VOLUME_PATTERN.search(part)
            if vol_match:
                tag = Tag(type='volume', value=vol_match.group(1), raw=part, description=f"量能大于{vol_match.group(1)}倍")
                tags.append(tag)
                parsed_structure['volume'].append(tag.model_dump())
                matched = True
                
            # Date
            date_match_cn = cls.DATE_PATTERN_CN.search(part)
            date_match_iso = cls.DATE_PATTERN_ISO.search(part)
            if date_match_cn or date_match_iso:
                d_str = ""
                if date_match_cn:
                    y, m, d = date_match_cn.groups()
                    d_str = f"{y}-{int(m):02d}-{int(d):02d}"
                else:
                    d_str = date_match_iso.group(0)
                
                # Check if it's today
                today_str = datetime.now().strftime('%Y-%m-%d')
                is_dynamic = (d_str == today_str)
                
                tag = Tag(type='date', value=d_str, raw=part, is_dynamic=is_dynamic, description="交易日期")
                tags.append(tag)
                parsed_structure['date'].append(tag.model_dump())
                matched = True
            
            # Block
            temp_part = part
            for block in cls.BLOCK_TAGS:
                if block in temp_part:
                    tag = Tag(type='block', value=block, raw=part, description=f"板块限制: {block}")
                    tags.append(tag)
                    parsed_structure['block'].append(tag.model_dump())
                    matched = True
                    # Remove matched block to avoid substring matching (e.g. avoid matching 'ST' in '非ST')
                    temp_part = temp_part.replace(block, "")
            
            # Concepts/Industry
            if "概念" in part or "行业" in part:
                tag = Tag(type='concept', value=part, raw=part, description="概念/行业")
                tags.append(tag)
                parsed_structure['concept'].append(tag.model_dump())
                matched = True
                
            # Fallback only if nothing matched
            if not matched:
                tag = Tag(type='other', value=part, raw=part)
                tags.append(tag)
                parsed_structure['other'].append(tag.model_dump())
            
        return {
            'tags': [t.model_dump() for t in tags],
            'structure': parsed_structure
        }

    @staticmethod
    def get_dynamic_query(original_query: str) -> str:
        """
        Replace dates in query with today's date to support daily automatic updates.
        """
        if not original_query:
            return ""
            
        today_cn = datetime.now().strftime('%Y年%m月%d日')
        today_iso = datetime.now().strftime('%Y-%m-%d')
        
        # Replace CN dates
        new_query = TagService.DATE_PATTERN_CN.sub(today_cn, original_query)
        # Replace ISO dates
        new_query = TagService.DATE_PATTERN_ISO.sub(today_iso, new_query)
        
        return new_query
    
    @staticmethod
    def validate_tags(tags: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate the consistency and rules of tags.
        """
        validation_results = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Example validation: Check for conflicting block tags
        block_values = [t['value'] for t in tags if t['type'] == 'block']
        if 'ST' in block_values and '非ST' in block_values:
            validation_results['valid'] = False
            validation_results['errors'].append("Conflict: Cannot have both 'ST' and '非ST'")
            
        # Example validation: Check date format
        for t in tags:
            if t['type'] == 'date':
                try:
                    datetime.strptime(t['value'], '%Y-%m-%d')
                except ValueError:
                    validation_results['valid'] = False
                    validation_results['errors'].append(f"Invalid date format: {t['value']}")

        return validation_results
