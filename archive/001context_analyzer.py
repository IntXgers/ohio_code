# analysis/title_context_analyzer.py
from core.model_manager import ModelManager
from core.web_research import WebResearcher
import json


class TitleContextAnalyzer:
    def __init__(self):
        self.manager = ModelManager()
        self.model = self.manager.load_model()
        self.lmdb = self.manager.load_lmdb()
        self.citations = self.manager.load_citation_map()
        self.researcher = WebResearcher()

    def analyze_title(self, title_num):
        """Full context analysis for a title"""

        # 1. Get all sections in this title
        title_sections = self._get_title_sections(title_num)

        # 2. Analyze citation patterns
        citation_analysis = self._analyze_citations(title_sections)

        # 3. Sample heavily referenced sections
        key_sections = self._get_key_sections(title_sections)

        # 4. Get web context (optional)
        web_context = self.researcher.search_ohio_law_context(title_num)

        # 5. Generate analysis with local model
        context = self._generate_context_analysis(
            title_sections,
            citation_analysis,
            key_sections,
            web_context
        )

        return context

    def _get_title_sections(self, title_num):
        """Extract all sections for a title from citations"""
        # Title 35 = sections 3501-3599
        start = int(f"{title_num}01")
        end = int(f"{title_num}99")

        title_sections = {}
        for section, refs in self.citations.items():
            try:
                section_num = float(section.replace('.', ''))
                if start <= section_num <= end:
                    title_sections[section] = refs
            except:
                continue
        return title_sections

    def _analyze_citations(self, sections):
        """Analyze citation patterns"""
        internal_refs = []
        external_refs = []

        for section, refs in sections.items():
            for ref in refs:
                if ref.startswith(section[:2]):  # Same title
                    internal_refs.append(ref)
                else:
                    external_refs.append(ref)

        return {
            'internal_count': len(internal_refs),
            'external_count': len(external_refs),
            'most_referenced': self._get_most_common(internal_refs),
            'external_titles': self._get_external_titles(external_refs)
        }

    def _generate_context_analysis(self, sections, citations, key_sections, web):
        """Use local model to analyze everything"""

        prompt = f"""
        Analyze Ohio Revised Code Title sections:

        Total sections: {len(sections)}
        Internal references: {citations['internal_count']}
        External references: {citations['external_count']}

        Sample key sections:
        {key_sections[:3]}

        Identify:
        1. Primary legal domains covered
        2. Key regulatory patterns
        3. Common requirements types
        4. Enforcement mechanisms
        5. Important cross-references
        """

        response = self.model(prompt, max_tokens=1000)
        return response['choices'][0]['text']