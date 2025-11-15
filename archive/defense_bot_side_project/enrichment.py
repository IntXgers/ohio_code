#!/usr/bin/env python3
"""
Defense Attorney Bot - Data Enrichment Pipeline
Transforms legal text into defense-focused training data
"""

import json
import logging
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import time
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
import hashlib
from tqdm import tqdm
import signal
import sys
from llama_cpp import Llama

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('defense_enrichment.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class DefenseConfig:
    """Configuration for defense attorney bot training"""
    # File paths
    input_file: str = "ohio_revised_code_complete.jsonl"
    case_law_dir: str = "data/raw/case_law"
    output_dir: str = "data/enriched"
    checkpoint_dir: str = "checkpoints"

    # Model settings
    model_path: str = "/path/to/model.gguf"
    model_context: int = 8192
    model_threads: int = 8
    max_tokens: int = 2000
    temperature: float = 0.3  # Lower for more consistent JSON

    # Processing settings
    batch_size: int = 10
    max_retries: int = 3
    num_workers: int = 1  # For parallel processing

    # Defense-specific settings
    defense_strategies: List[str] = field(default_factory=lambda: [
        "constitutional_challenges",
        "procedural_defects",
        "evidentiary_issues",
        "affirmative_defenses",
        "mitigation_factors",
        "plea_negotiations",
        "jury_psychology"
    ])


class DefenseKnowledgeBase:
    """Core defense attorney knowledge and strategies"""

    CONSTITUTIONAL_RIGHTS = {
        "4th_amendment": {
            "right": "Protection against unreasonable searches and seizures",
            "applications": [
                "Motion to suppress illegally obtained evidence",
                "Challenge warrantless searches",
                "Attack probable cause determinations",
                "Fruit of the poisonous tree doctrine"
            ]
        },
        "5th_amendment": {
            "right": "Protection against self-incrimination",
            "applications": [
                "Miranda violations",
                "Coerced confessions",
                "Double jeopardy",
                "Due process violations"
            ]
        },
        "6th_amendment": {
            "right": "Right to counsel and fair trial",
            "applications": [
                "Ineffective assistance of counsel",
                "Right to confront witnesses",
                "Speedy trial violations",
                "Jury selection issues"
            ]
        }
    }

    DEFENSE_STRATEGIES = {
        "pre_trial": [
            "Motion to dismiss for lack of probable cause",
            "Motion to suppress evidence",
            "Discovery demands",
            "Speedy trial demands",
            "Change of venue motions"
        ],
        "trial": [
            "Jury nullification",
            "Alternative theory of the case",
            "Attacking witness credibility",
            "Creating reasonable doubt",
            "Expert witness challenges"
        ],
        "post_trial": [
            "Motion for new trial",
            "Appeal grounds",
            "Ineffective assistance claims",
            "Sentence mitigation"
        ]
    }

    COMMON_DEFENSES = {
        "general": [
            "Lack of intent",
            "Mistake of fact",
            "Alibi",
            "Misidentification",
            "False accusation"
        ],
        "affirmative": [
            "Self-defense",
            "Defense of others",
            "Necessity",
            "Duress",
            "Entrapment",
            "Insanity"
        ]
    }


class DefenseEnricher:
    def __init__(self, config: DefenseConfig):
        self.config = config
        self.knowledge = DefenseKnowledgeBase()
        self.output_dir = Path(config.output_dir)
        self.checkpoint_dir = Path(config.checkpoint_dir)

        # Create directories
        for dir_path in [self.output_dir, self.checkpoint_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Initialize model
        self._init_model()

        # Load checkpoint
        self.checkpoint_file = self.checkpoint_dir / "defense_enrichment_checkpoint.json"
        self.processed_items = self._load_checkpoint()

        # Setup graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)

    def _init_model(self):
        """Initialize the LLM model"""
        logger.info(f"Loading model from: {self.config.model_path}")
        try:
            self.model = Llama(
                model_path=str(self.config.model_path),
                n_ctx=self.config.model_context,
                n_threads=self.config.model_threads,
                verbose=False,
                n_gpu_layers=-1  # Use all GPU layers
            )
            logger.info("✅ Model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def _signal_handler(self, signum, frame):
        """Handle graceful shutdown"""
        logger.info("\n🛑 Interrupt received, saving checkpoint...")
        self._save_checkpoint()
        sys.exit(0)

    def _load_checkpoint(self) -> set:
        """Load processing checkpoint"""
        if self.checkpoint_file.exists():
            with open(self.checkpoint_file, 'r') as f:
                data = json.load(f)
                logger.info(f"Resuming from checkpoint: {data['processed_count']} items processed")
                return set(data['processed_items'])
        return set()

    def _save_checkpoint(self):
        """Save processing checkpoint"""
        checkpoint_data = {
            'processed_count': len(self.processed_items),
            'processed_items': list(self.processed_items),
            'timestamp': datetime.now().isoformat()
        }
        with open(self.checkpoint_file, 'w') as f:
            json.dump(checkpoint_data, f, indent=2)

    def _get_item_hash(self, item: Dict[str, Any]) -> str:
        """Create unique hash for an item"""
        content = f"{item.get('header', '')}_{item.get('paragraphs', '')}"
        return hashlib.md5(content.encode()).hexdigest()

    def clean_json_response(self, text: str) -> str:
        """Extract valid JSON from LLM response"""
        # Remove markdown
        text = text.replace("```json", "").replace("```", "")

        # Find JSON boundaries using bracket/brace matching
        def find_json_bounds(text: str, open_char: str, close_char: str) -> Optional[Tuple[int, int]]:
            start = text.find(open_char)
            if start == -1:
                return None

            count = 0
            for i in range(start, len(text)):
                if text[i] == open_char:
                    count += 1
                elif text[i] == close_char:
                    count -= 1
                    if count == 0:
                        return (start, i + 1)
            return None

        # Try to extract JSON array or object
        for open_char, close_char in [('[', ']'), ('{', '}')]:
            bounds = find_json_bounds(text, open_char, close_char)
            if bounds:
                return text[bounds[0]:bounds[1]]

        return text.strip()

    def generate_with_retry(self, prompt: str, expected_format: str = "object") -> Optional[Any]:
        """Generate LLM response with retries"""
        for attempt in range(self.config.max_retries):
            try:
                response = self.model(
                    prompt,
                    max_tokens=self.config.max_tokens,
                    temperature=self.config.temperature,
                    stop=["Human:", "User:", "\n\n\n", "}\n]", "]\n", "}\n\n"]
                )

                text = response['choices'][0]['text'].strip()
                cleaned = self.clean_json_response(text)
                result = json.loads(cleaned)

                # Validate structure
                if expected_format == "object" and isinstance(result, dict):
                    return result
                elif expected_format == "array" and isinstance(result, list):
                    return result
                else:
                    logger.warning(f"Unexpected format on attempt {attempt + 1}")

            except json.JSONDecodeError as e:
                logger.warning(f"JSON parse error on attempt {attempt + 1}: {e}")
                if attempt == 0:
                    logger.debug(f"Raw response: {text[:500]}...")
            except Exception as e:
                logger.warning(f"Generation error on attempt {attempt + 1}: {e}")

            if attempt < self.config.max_retries - 1:
                time.sleep(1)

        return None

    def create_defense_scenario_prompt(self, header: str, content: str) -> str:
        """Create defense scenarios for a statute"""
        return f"""As an experienced defense attorney, create 4 realistic scenarios where someone charged under this statute could mount a strong defense.

Statute: {header}
Content: {content[:1000]}...

For each scenario, provide:
1. A case where the facts initially look bad but there's reasonable doubt
2. A case with constitutional violations (4th, 5th, or 6th Amendment)
3. A case where an affirmative defense applies
4. A case with significant mitigation factors

Return ONLY a JSON array with exactly 4 scenarios:
[
  {{
    "scenario_type": "reasonable_doubt",
    "facts": "Brief case facts",
    "initial_problem": "Why it looks bad for defendant",
    "defense_strategy": "How to create reasonable doubt",
    "key_arguments": ["argument1", "argument2"],
    "potential_outcome": "Likely result"
  }},
  // ... 3 more scenarios
]

Focus on realistic, winnable defenses. NO additional text outside the JSON."""

    def create_constitutional_analysis_prompt(self, header: str, content: str) -> str:
        """Analyze constitutional issues in enforcement"""
        return f"""Analyze potential constitutional challenges to enforcement of this statute from a defense perspective.

Statute: {header}
Content: {content[:800]}...

Return ONLY this JSON structure:
{{
  "fourth_amendment_issues": [
    {{
      "issue": "Specific 4th Amendment concern",
      "motion": "Motion to file",
      "argument": "Legal argument"
    }}
  ],
  "fifth_amendment_issues": [
    {{
      "issue": "Specific 5th Amendment concern",
      "context": "When this applies",
      "remedy": "Legal remedy"
    }}
  ],
  "sixth_amendment_issues": [
    {{
      "issue": "Specific 6th Amendment concern",
      "impact": "Effect on case"
    }}
  ],
  "due_process_concerns": [
    {{
      "issue": "Due process problem",
      "challenge": "How to challenge"
    }}
  ],
  "vagueness_overbreadth": {{
    "is_vague": true/false,
    "vague_terms": ["term1", "term2"],
    "overbreadth_issues": "Analysis if applicable"
  }}
}}"""

    def create_evidence_challenge_prompt(self, header: str, content: str) -> str:
        """Generate evidence suppression strategies"""
        return f"""As a defense attorney, identify ways to challenge evidence in prosecutions under this statute.

Statute: {header}
Content: {content[:800]}...

Return ONLY this JSON structure:
{{
  "common_evidence_types": [
    {{
      "evidence_type": "Type of evidence typically used",
      "suppression_grounds": ["ground1", "ground2"],
      "motion_strategy": "Specific motion to file",
      "voir_dire_questions": ["question for challenging this evidence"]
    }}
  ],
  "chain_of_custody_issues": [
    "Potential break point 1",
    "Potential break point 2"
  ],
  "expert_testimony_challenges": [
    {{
      "expert_type": "Type of expert witness",
      "daubert_challenges": ["challenge1", "challenge2"],
      "cross_examination_topics": ["topic1", "topic2"]
    }}
  ],
  "discovery_demands": [
    "Specific item to demand",
    "Brady material to request"
  ]
}}"""

    def create_jury_strategy_prompt(self, header: str, content: str) -> str:
        """Create jury selection and argument strategies"""
        return f"""Develop jury strategies for defending against charges under this statute.

Statute: {header}
Content: {content[:600]}...

Return ONLY this JSON structure:
{{
  "ideal_juror_profile": {{
    "demographics": "General characteristics",
    "experiences": ["relevant life experiences"],
    "attitudes": ["helpful attitudes/beliefs"]
  }},
  "voir_dire_questions": [
    {{
      "question": "Specific voir dire question",
      "purpose": "What this reveals",
      "follow_up": "If concerning answer"
    }}
  ],
  "theme_theory": {{
    "case_theme": "One sentence theme",
    "theory": "Theory of defense",
    "story": "Narrative arc for jury"
  }},
  "closing_arguments": [
    "Key point 1 for closing",
    "Key point 2 for closing",
    "Emotional appeal"
  ],
  "jury_instructions": [
    {{
      "instruction": "Specific instruction to request",
      "importance": "Why this helps defense"
    }}
  ]
}}"""

    def create_negotiation_prompt(self, header: str, content: str) -> str:
        """Create plea negotiation strategies"""
        return f"""Develop plea negotiation strategies for charges under this statute.

Statute: {header}
Content: {content[:600]}...

Return ONLY this JSON structure:
{{
  "charge_analysis": {{
    "severity_level": "felony/misdemeanor level",
    "mandatory_minimums": "any mandatory sentences",
    "collateral_consequences": ["consequence1", "consequence2"]
  }},
  "negotiation_leverage": [
    {{
      "leverage_point": "Weakness in state's case",
      "how_to_use": "Negotiation approach"
    }}
  ],
  "alternative_dispositions": [
    {{
      "option": "Alternative to conviction",
      "requirements": "What client must do",
      "benefits": "Why this is better"
    }}
  ],
  "lesser_included_offenses": [
    {{
      "offense": "Lesser charge name",
      "elements_difference": "What state can't prove",
      "sentence_reduction": "Benefit to client"
    }}
  ],
  "mitigation_presentation": {{
    "client_background": ["factors to emphasize"],
    "expert_support": "Type of expert to consider",
    "victim_consideration": "Approach if victim involved"
  }}
}}"""

    def create_cross_examination_prompt(self, header: str, content: str) -> str:
        """Generate cross-examination strategies"""
        return f"""Create cross-examination strategies for common witnesses in prosecutions under this statute.

Statute: {header}
Content: {content[:600]}...

Return ONLY this JSON structure:
{{
  "officer_cross": [
    {{
      "topic": "Area to probe",
      "questions": [
        "Leading question 1",
        "Leading question 2"
      ],
      "impeachment": "If officer says X, show Y"
    }}
  ],
  "expert_cross": [
    {{
      "qualification_challenges": ["question about credentials"],
      "methodology_attacks": ["question about methods"],
      "bias_exploration": ["question about payment/bias"]
    }}
  ],
  "civilian_witness_cross": [
    {{
      "perception_issues": "Questions about ability to perceive",
      "memory_challenges": "Questions about memory",
      "bias_questions": "Questions about relationship/motive"
    }}
  ],
  "common_objections": [
    {{
      "state_tactic": "What prosecution might do",
      "objection": "Specific objection to make",
      "argument": "Supporting argument"
    }}
  ]
}}"""

    def process_single_statute(self, doc: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a single statute with all defense enrichments"""
        header = doc.get('header', '')
        paragraphs = doc.get('paragraphs', [])

        if not header or not paragraphs:
            return None

        # Check if already processed
        item_hash = self._get_item_hash(doc)
        if item_hash in self.processed_items:
            logger.debug(f"Skipping already processed: {header[:50]}...")
            return None

        content = ' '.join(paragraphs) if isinstance(paragraphs, list) else str(paragraphs)

        if len(content) < 50:
            logger.warning(f"Skipping short content: {header}")
            return None

        logger.info(f"Processing: {header[:80]}...")

        enriched = {
            'original': doc,
            'processed_at': datetime.now().isoformat(),
            'enrichment_version': '2.0',
            'defense_focused': True
        }

        # Generate all defense-specific content
        enrichments = [
            ('defense_scenarios', self.create_defense_scenario_prompt, 'array'),
            ('constitutional_analysis', self.create_constitutional_analysis_prompt, 'object'),
            ('evidence_challenges', self.create_evidence_challenge_prompt, 'object'),
            ('jury_strategy', self.create_jury_strategy_prompt, 'object'),
            ('negotiation_strategy', self.create_negotiation_prompt, 'object'),
            ('cross_examination', self.create_cross_examination_prompt, 'object')
        ]

        for key, prompt_func, expected_format in enrichments:
            result = self.generate_with_retry(
                prompt_func(header, content),
                expected_format=expected_format
            )
            enriched[key] = result or ({} if expected_format == 'object' else [])

        # Mark as processed
        self.processed_items.add(item_hash)

        return enriched

    def save_training_formats(self, enriched_data: List[Dict[str, Any]], stage: str):
        """Save data in multiple training formats optimized for defense attorney bot"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stage_dir = self.output_dir / f"stage_{stage}"
        stage_dir.mkdir(exist_ok=True)

        # 1. Defense Scenarios Format (for scenario reasoning)
        scenarios_data = []
        for doc in enriched_data:
            for scenario in doc.get('defense_scenarios', []):
                scenarios_data.append({
                    'instruction': f"I'm charged under {doc['original']['header']}. The facts are: {scenario.get('facts', '')}",
                    'response': f"Based on these facts, {scenario.get('defense_strategy', '')}. Key arguments include: {', '.join(scenario.get('key_arguments', []))}",
                    'metadata': {
                        'scenario_type': scenario.get('scenario_type', ''),
                        'statute': doc['original']['header']
                    }
                })

        # 2. Constitutional Challenge Format
        constitutional_data = []
        for doc in enriched_data:
            analysis = doc.get('constitutional_analysis', {})

            # 4th Amendment
            for issue in analysis.get('fourth_amendment_issues', []):
                constitutional_data.append({
                    'instruction': f"What 4th Amendment issues exist with enforcement of {doc['original']['header']}?",
                    'response': f"{issue.get('issue', '')}. File a {issue.get('motion', '')} arguing: {issue.get('argument', '')}",
                    'metadata': {'amendment': '4th', 'statute': doc['original']['header']}
                })

        # 3. Evidence Challenge Format
        evidence_data = []
        for doc in enriched_data:
            evidence = doc.get('evidence_challenges', {})
            for evt in evidence.get('common_evidence_types', []):
                evidence_data.append({
                    'instruction': f"How do I challenge {evt.get('evidence_type', '')} evidence in a {doc['original']['header']} case?",
                    'response': f"File a {evt.get('motion_strategy', '')} based on: {', '.join(evt.get('suppression_grounds', []))}",
                    'metadata': {'evidence_type': evt.get('evidence_type', ''), 'statute': doc['original']['header']}
                })

        # 4. Jury Strategy Format
        jury_data = []
        for doc in enriched_data:
            strategy = doc.get('jury_strategy', {})
            if strategy.get('theme_theory', {}):
                jury_data.append({
                    'instruction': f"What's the best defense theme for a {doc['original']['header']} charge?",
                    'response': f"Theme: {strategy['theme_theory'].get('case_theme', '')}. Theory: {strategy['theme_theory'].get('theory', '')}",
                    'metadata': {'type': 'theme', 'statute': doc['original']['header']}
                })

        # 5. Combined ChatML Format (for conversational fine-tuning)
        chatml_data = []
        for doc in enriched_data:
            # Create a multi-turn conversation using all enrichments
            messages = [
                {"role": "system",
                 "content": "You are an experienced criminal defense attorney in Ohio. Provide strategic legal advice while protecting client rights."},
                {"role": "user",
                 "content": f"I've been charged under {doc['original']['header']}. What should I know?"},
                {"role": "assistant", "content": self._create_comprehensive_response(doc)}
            ]

            # Add follow-up Q&A
            if doc.get('defense_scenarios'):
                messages.extend([
                    {"role": "user", "content": "What defenses might apply to my case?"},
                    {"role": "assistant", "content": self._create_defense_summary(doc)}
                ])

            chatml_data.append({
                'messages': messages,
                'metadata': {'statute': doc['original']['header'], 'type': 'comprehensive'}
            })

        # Save all formats
        formats = {
            'scenarios': scenarios_data,
            'constitutional': constitutional_data,
            'evidence': evidence_data,
            'jury': jury_data,
            'chatml': chatml_data
        }

        for format_name, data in formats.items():
            if data:  # Only save if there's data
                output_file = stage_dir / f"{format_name}_{timestamp}.jsonl"
                with open(output_file, 'w', encoding='utf-8') as f:
                    for item in data:
                        f.write(json.dumps(item, ensure_ascii=False) + '\n')
                logger.info(f"Saved {len(data)} examples to {format_name} format")

        # Save complete enriched data
        full_file = stage_dir / f"enriched_complete_{timestamp}.jsonl"
        with open(full_file, 'w', encoding='utf-8') as f:
            for item in enriched_data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')

        # Log statistics
        logger.info(f"Stage {stage} complete:")
        logger.info(f"  - Scenarios: {len(scenarios_data)}")
        logger.info(f"  - Constitutional: {len(constitutional_data)}")
        logger.info(f"  - Evidence: {len(evidence_data)}")
        logger.info(f"  - Jury: {len(jury_data)}")
        logger.info(f"  - ChatML: {len(chatml_data)}")

    def _create_comprehensive_response(self, doc: Dict[str, Any]) -> str:
        """Create a comprehensive initial response for a statute"""
        scenarios = doc.get('defense_scenarios', [])
        constitutional = doc.get('constitutional_analysis', {})

        response = f"Understanding charges under {doc['original']['header']} requires analyzing several key areas:\n\n"

        if scenarios:
            response += "**Potential Defenses:**\n"
            for s in scenarios[:2]:  # First two scenarios
                response += f"- {s.get('scenario_type', '')}: {s.get('defense_strategy', '')}\n"

        if constitutional.get('vagueness_overbreadth', {}).get('is_vague'):
            response += f"\n**Constitutional Concerns:** This statute may be challengeable for vagueness regarding terms: {', '.join(constitutional['vagueness_overbreadth'].get('vague_terms', []))}\n"

        response += "\nI recommend immediately: (1) Demanding all discovery, (2) Filing any applicable motions to suppress, (3) Investigating lesser included offenses."

        return response

    def _create_defense_summary(self, doc: Dict[str, Any]) -> str:
        """Create a defense summary from scenarios"""
        scenarios = doc.get('defense_scenarios', [])
        if not scenarios:
            return "We need to review the specific facts of your case to identify the best defense strategy."

        response = "Based on this statute, several defenses may apply:\n\n"
        for i, scenario in enumerate(scenarios, 1):
            response += f"{i}. **{scenario.get('scenario_type', '').replace('_', ' ').title()}**: "
            response += f"{scenario.get('defense_strategy', '')}\n"
            response += f"   Key arguments: {', '.join(scenario.get('key_arguments', []))}\n\n"

        return response

    def process_all_statutes(self):
        """Process all statutes with progress tracking and checkpointing"""
        input_path = Path(self.config.input_file)
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")

        # Count total documents
        total_docs = sum(1 for _ in open(input_path, 'r', encoding='utf-8'))
        already_processed = len(self.processed_items)

        logger.info(f"Total documents: {total_docs}")
        logger.info(f"Already processed: {already_processed}")
        logger.info(f"Remaining: {total_docs - already_processed}")

        enriched_batch = []
        processed_count = 0
        error_count = 0

        with open(input_path, 'r', encoding='utf-8') as f:
            # Use tqdm for progress bar
            lines = f.readlines()
            for line in tqdm(lines, desc="Processing statutes", total=total_docs):
                try:
                    doc = json.loads(line.strip())

                    # Skip if already processed
                    if self._get_item_hash(doc) in self.processed_items:
                        continue

                    enriched = self.process_single_statute(doc)

                    if enriched:
                        enriched_batch.append(enriched)
                        processed_count += 1

                        # Save batch and checkpoint
                        if len(enriched_batch) >= self.config.batch_size:
                            self.save_training_formats(enriched_batch, "1_statutory")
                            self._save_checkpoint()
                            enriched_batch = []

                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse line: {e}")
                    error_count += 1
                except Exception as e:
                    logger.error(f"Error processing document: {e}")
                    error_count += 1

        # Save final batch
        if enriched_batch:
            self.save_training_formats(enriched_batch, "1_statutory")
            self._save_checkpoint()

        logger.info(f"\n✅ Processing complete!")
        logger.info(f"   Processed: {processed_count} documents")
        logger.info(f"   Errors: {error_count}")
        logger.info(f"   Output directory: {self.output_dir}")


def create_config_file():
    """Create a sample configuration file"""
    config = {
        'model': {
            'path': '/path/to/your/model.gguf',
            'context_length': 8192,
            'threads': 8,
            'gpu_layers': -1
        },
        'processing': {
            'batch_size': 10,
            'max_retries': 3,
            'temperature': 0.3,
            'max_tokens': 2000
        },
        'paths': {
            'input_file': 'ohio_revised_code_complete.jsonl',
            'case_law_dir': 'data/raw/case_law',
            'output_dir': 'data/enriched',
            'checkpoint_dir': 'checkpoints'
        },
        'defense_focus': {
            'include_scenarios': True,
            'include_constitutional': True,
            'include_evidence': True,
            'include_jury': True,
            'include_negotiation': True,
            'include_cross_examination': True
        }
    }

    with open('defense_config.yaml', 'w') as f:
        yaml.dump(config, f, default_flow_style=False)

    logger.info("Created sample configuration file: defense_config.yaml")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Defense Attorney Bot Data Enrichment')
    parser.add_argument('--config', type=str, help='Path to configuration file')
    parser.add_argument('--create-config', action='store_true', help='Create sample config file')
    parser.add_argument('--input', type=str, help='Input JSONL file')
    parser.add_argument('--model', type=str, help='Path to model file')
    parser.add_argument('--batch-size', type=int, default=10, help='Batch size for processing')

    args = parser.parse_args()

    if args.create_config:
        create_config_file()
        return

    # Load configuration
    if args.config and Path(args.config).exists():
        with open(args.config, 'r') as f:
            config_data = yaml.safe_load(f)
            config = DefenseConfig(
                input_file=config_data['paths']['input_file'],
                model_path=config_data['model']['path'],
                model_context=config_data['model']['context_length'],
                model_threads=config_data['model']['threads'],
                batch_size=config_data['processing']['batch_size'],
                temperature=config_data['processing']['temperature'],
                max_tokens=config_data['processing']['max_tokens']
            )
    else:
        # Use command line arguments or defaults
        config = DefenseConfig(
            input_file=args.input or "ohio_revised_code_complete.jsonl",
            model_path=args.model or "/path/to/model.gguf",
            batch_size=args.batch_size
        )

    try:
        enricher = DefenseEnricher(config)
        enricher.process_all_statutes()
    except KeyboardInterrupt:
        logger.info("\n🛑 Processing interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise


if __name__ == "__main__":
    main()