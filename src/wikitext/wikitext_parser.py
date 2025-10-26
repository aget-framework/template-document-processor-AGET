"""Wikitext Parser for GM-RKB Format Documents

Parses Wikitext markup used in MediaWiki-based wikis (like GM-RKB).

Handles:
- Headings and sections
- Templates and transclusions
- Links (internal and external)
- Lists and formatting
- Categories and metadata

Note: This is a template implementation with basic parsing.
Production use should consider wikitextparser or mwparserfromhell libraries.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import re


@dataclass
class WikiSection:
    """Represents a section in wiki document"""
    title: str
    level: int  # 1-6 (= to ======)
    content: str
    subsections: List['WikiSection']


@dataclass
class WikiLink:
    """Represents a wikilink"""
    target: str
    display_text: Optional[str] = None
    is_external: bool = False


@dataclass
class WikiTemplate:
    """Represents a template transclusion"""
    name: str
    parameters: Dict[str, str]


class WikitextParser:
    """Parser for Wikitext markup

    Provides basic parsing of common Wikitext constructs.

    Design Decision: Simple regex-based parsing for template.
    Production should use dedicated libraries:
    - wikitextparser: https://github.com/5j9/wikitextparser
    - mwparserfromhell: https://github.com/earwig/mwparserfromhell

    Note: This parser handles GM-RKB specific patterns but
    is extensible for other MediaWiki-based wikis.
    """

    def __init__(self):
        """Initialize wikitext parser"""
        pass

    def parse(self, wikitext: str) -> Dict:
        """Parse wikitext into structured format

        Args:
            wikitext: Raw wikitext content

        Returns:
            Dictionary with parsed components
        """
        return {
            'sections': self.extract_sections(wikitext),
            'links': self.extract_links(wikitext),
            'templates': self.extract_templates(wikitext),
            'categories': self.extract_categories(wikitext),
            'plain_text': self.to_plain_text(wikitext)
        }

    def extract_sections(self, wikitext: str) -> List[WikiSection]:
        """Extract sections from wikitext

        Args:
            wikitext: Raw wikitext

        Returns:
            List of WikiSection objects
        """
        sections = []

        # Pattern: ==Title== (level 2) to ======Title====== (level 6)
        heading_pattern = r'^(={2,6})\s*(.+?)\s*\1\s*$'

        lines = wikitext.split('\n')
        current_section = None
        current_content = []

        for line in lines:
            match = re.match(heading_pattern, line, re.MULTILINE)

            if match:
                # Save previous section
                if current_section:
                    current_section.content = '\n'.join(current_content)
                    sections.append(current_section)

                # Start new section
                level = len(match.group(1))
                title = match.group(2).strip()

                current_section = WikiSection(
                    title=title,
                    level=level,
                    content='',
                    subsections=[]
                )
                current_content = []
            else:
                if current_section:
                    current_content.append(line)

        # Save final section
        if current_section:
            current_section.content = '\n'.join(current_content)
            sections.append(current_section)

        return sections

    def extract_links(self, wikitext: str) -> List[WikiLink]:
        """Extract links from wikitext

        Args:
            wikitext: Raw wikitext

        Returns:
            List of WikiLink objects
        """
        links = []

        # Internal links: [[Target]] or [[Target|Display]]
        internal_pattern = r'\[\[([^\]|]+)(?:\|([^\]]+))?\]\]'
        for match in re.finditer(internal_pattern, wikitext):
            target = match.group(1).strip()
            display = match.group(2).strip() if match.group(2) else None

            links.append(WikiLink(
                target=target,
                display_text=display,
                is_external=False
            ))

        # External links: [http://example.com Display]
        external_pattern = r'\[(https?://[^\s\]]+)(?:\s+([^\]]+))?\]'
        for match in re.finditer(external_pattern, wikitext):
            url = match.group(1)
            display = match.group(2) if match.group(2) else None

            links.append(WikiLink(
                target=url,
                display_text=display,
                is_external=True
            ))

        return links

    def extract_templates(self, wikitext: str) -> List[WikiTemplate]:
        """Extract templates from wikitext

        Templates format: {{TemplateName|param1=value1|param2=value2}}

        Args:
            wikitext: Raw wikitext

        Returns:
            List of WikiTemplate objects
        """
        templates = []

        # Simple template extraction (doesn't handle nested templates)
        template_pattern = r'\{\{([^{}|]+)(?:\|([^{}]+))?\}\}'

        for match in re.finditer(template_pattern, wikitext):
            name = match.group(1).strip()
            params_str = match.group(2) if match.group(2) else ""

            # Parse parameters
            params = {}
            if params_str:
                param_parts = params_str.split('|')
                for i, part in enumerate(param_parts):
                    part = part.strip()
                    if '=' in part:
                        key, value = part.split('=', 1)
                        params[key.strip()] = value.strip()
                    else:
                        # Positional parameter
                        params[str(i + 1)] = part

            templates.append(WikiTemplate(
                name=name,
                parameters=params
            ))

        return templates

    def extract_categories(self, wikitext: str) -> List[str]:
        """Extract categories from wikitext

        Categories format: [[Category:CategoryName]]

        Args:
            wikitext: Raw wikitext

        Returns:
            List of category names
        """
        categories = []

        category_pattern = r'\[\[Category:([^\]|]+)(?:\|[^\]]+)?\]\]'
        for match in re.finditer(category_pattern, wikitext, re.IGNORECASE):
            categories.append(match.group(1).strip())

        return categories

    def to_plain_text(self, wikitext: str) -> str:
        """Convert wikitext to plain text

        Removes wiki markup to get readable text.

        Args:
            wikitext: Raw wikitext

        Returns:
            Plain text without markup
        """
        text = wikitext

        # Remove templates
        text = re.sub(r'\{\{[^{}]+\}\}', '', text)

        # Remove comments
        text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)

        # Convert links to text
        text = re.sub(r'\[\[(?:[^\]|]+\|)?([^\]]+)\]\]', r'\1', text)  # [[Link|Text]] -> Text
        text = re.sub(r'\[https?://[^\s\]]+ ([^\]]+)\]', r'\1', text)  # [URL Text] -> Text

        # Remove formatting
        text = re.sub(r"'''", '', text)  # Bold
        text = re.sub(r"''", '', text)   # Italic

        # Remove headings markup
        text = re.sub(r'^={2,6}\s*(.+?)\s*={2,6}\s*$', r'\1', text, flags=re.MULTILINE)

        # Remove categories
        text = re.sub(r'\[\[Category:[^\]]+\]\]', '', text, flags=re.IGNORECASE)

        # Clean up whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = text.strip()

        return text

    def extract_infobox(self, wikitext: str) -> Optional[Dict[str, str]]:
        """Extract infobox data if present

        Infobox format: {{Infobox ...|field1=value1|field2=value2}}

        Args:
            wikitext: Raw wikitext

        Returns:
            Dictionary with infobox fields or None
        """
        # Pattern for infobox
        infobox_pattern = r'\{\{Infobox[^{]*?\|([^{}]+)\}\}'

        match = re.search(infobox_pattern, wikitext, re.IGNORECASE | re.DOTALL)

        if not match:
            return None

        # Parse infobox fields
        fields_str = match.group(1)
        fields = {}

        field_parts = fields_str.split('|')
        for part in field_parts:
            part = part.strip()
            if '=' in part:
                key, value = part.split('=', 1)
                fields[key.strip()] = value.strip()

        return fields


class GMRKBParser(WikitextParser):
    """Specialized parser for GM-RKB (General Multilingual RKB) format

    Extends WikitextParser with GM-RKB specific patterns.

    GM-RKB typically includes:
    - Research knowledge entities
    - Semantic relationships
    - Structured metadata
    """

    def parse_research_entity(self, wikitext: str) -> Dict:
        """Parse research entity from GM-RKB format

        Args:
            wikitext: Raw wikitext

        Returns:
            Dictionary with entity information
        """
        base_parse = self.parse(wikitext)

        # Extract GM-RKB specific metadata
        entity = {
            'type': self._extract_entity_type(wikitext),
            'metadata': self._extract_metadata(wikitext),
            'relationships': self._extract_relationships(wikitext),
            **base_parse
        }

        return entity

    def _extract_entity_type(self, wikitext: str) -> Optional[str]:
        """Extract entity type from GM-RKB markup

        Args:
            wikitext: Raw wikitext

        Returns:
            Entity type or None
        """
        # Look for entity type in categories
        categories = self.extract_categories(wikitext)

        # Common GM-RKB entity types
        entity_types = ['Person', 'Organization', 'Event', 'Publication', 'Concept']

        for category in categories:
            for entity_type in entity_types:
                if entity_type.lower() in category.lower():
                    return entity_type

        return None

    def _extract_metadata(self, wikitext: str) -> Dict:
        """Extract structured metadata

        Args:
            wikitext: Raw wikitext

        Returns:
            Dictionary with metadata fields
        """
        metadata = {}

        # Try to extract from infobox
        infobox = self.extract_infobox(wikitext)
        if infobox:
            metadata.update(infobox)

        return metadata

    def _extract_relationships(self, wikitext: str) -> List[Tuple[str, str, str]]:
        """Extract semantic relationships

        Args:
            wikitext: Raw wikitext

        Returns:
            List of (subject, predicate, object) tuples
        """
        relationships = []

        # Extract from structured sections
        sections = self.extract_sections(wikitext)

        for section in sections:
            # Look for relationship-indicating sections
            if any(keyword in section.title.lower() for keyword in ['relation', 'link', 'connect']):
                # Extract links from this section as relationships
                links = self.extract_links(section.content)
                for link in links:
                    relationships.append((
                        'entity',  # Subject (current entity)
                        section.title,  # Predicate (relationship type)
                        link.target  # Object (linked entity)
                    ))

        return relationships
