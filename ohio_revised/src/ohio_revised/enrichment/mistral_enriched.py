#!/usr/bin/env python3
"""
LLM-Powered Legal Data Processor
Transforms { "url": "...", "header": "...", "paragraphs": [...], "url_hash": "..." }
into rich fine-tuning datasets using AI analysis
"""

import json
import re
from pathlib import Path
from typing import List,Dict,Any,Optional
from datetime import datetime
from llama_cpp import Llama


class LegalDataProcessor:
    def __init__ (self,model_path: str):
        """Initialize with local GGUF model for LLM analysis"""
        print (f"🚀 Loading model: {model_path}")
        self.model = Llama (
            model_path=model_path,
            n_ctx=4096,
            n_threads=4,
            verbose=False
            )
        print ("✅ Model loaded successfully!")

    def generate_response (self,prompt: str,max_tokens: int = 300) -> str:
        """Generate LLM response for analysis"""
        try:
            response = self.model (
                prompt,
                max_tokens=max_tokens,
                temperature=0.7,
                stop=["User:","Human:","\n\n"],
                echo=False
                )
            return response ['choices'] [0] ['text'].strip ()
        except Exception as e:
            print (f"   ⚠️ Generation error: {e}")
            return ""

    def extract_section_info (self,header: str) -> tuple [str,str]:
        """Extract section number and title from header"""
        if "|" in header:
            parts = header.split ("|",1)
            section_match = re.search (r'Section\s+(\d+\.\d+)',parts [0])
            section_number = section_match.group (1) if section_match else "unknown"
            title = parts [1].strip () if len (parts) > 1 else "Untitled"
        else:
            section_match = re.search (r'Section\s+(\d+\.\d+)',header)
            section_number = section_match.group (1) if section_match else "unknown"
            title = header.replace ("Section","").strip ()

        return section_number,title

    def combine_paragraphs (self,paragraphs: List [str]) -> str:
        """Combine paragraph list into single content string"""
        if isinstance (paragraphs,list):
            return " ".join (paragraphs)
        return str (paragraphs)

    def extract_legal_concepts_with_llm (self,content: str) -> Dict [str,Any]:
        """Use LLM to intelligently extract legal concepts"""
        prompt = f"""Analyze this legal text and extract key information in JSON format:

TEXT: {content [:1000]}

Extract and return JSON with:
- legal_entities: List of government entities, roles, positions mentioned
- procedures: List of procedural steps or processes described  
- requirements: List of legal requirements or obligations
- key_concepts: List of important legal concepts or terms
- legal_domain: Single category (legislative_procedure, criminal_law, civil_procedure, etc.)
- complexity_score: Integer 1-10 based on legal complexity

Return only valid JSON with this structure."""

        try:
            response = self.generate_response (prompt,400)
            # Clean response for JSON parsing
            response = self.clean_json_response (response)

            if response:
                try:
                    return json.loads (response)
                except json.JSONDecodeError:
                    pass

            # Fallback analysis if LLM fails
            return self.fallback_analysis (content)

        except Exception as e:
            print (f"   ⚠️ Error in LLM analysis: {e}")
            return self.fallback_analysis (content)

    def clean_json_response (self,response: str) -> str:
        """Clean LLM response to ensure valid JSON"""
        response = response.strip ()

        # Remove markdown code blocks
        if response.startswith ('```json'):
            response = response.replace ('```json','').replace ('```','').strip ()
        elif response.startswith ('```'):
            response = response.replace ('```','').strip ()

        # Find JSON content between first { and last }
        start = response.find ('{')
        end = response.rfind ('}')

        if start != -1 and end != -1:
            return response [start:end + 1]

        return response

    def fallback_analysis (self,content: str) -> Dict [str,Any]:
        """Fallback analysis if LLM fails"""
        content_lower = content.lower ()

        # Basic entity extraction
        entities = []
        entity_patterns = [
            r'\b(assembly|house|senate|committee|board|commission|department)\b',
            r'\b(governor|speaker|president|clerk|member|representative)\b'
            ]

        for pattern in entity_patterns:
            matches = re.findall (pattern,content_lower)
            entities.extend (matches)

        # Determine domain by content analysis
        if any (word in content_lower for word in ['criminal','arrest','prosecution']):
            domain = "criminal_law"
        elif any (word in content_lower for word in ['election','voting','legislative']):
            domain = "legislative_procedure"
        elif any (word in content_lower for word in ['tax','revenue','levy']):
            domain = "tax_law"
        elif any (word in content_lower for word in ['procedure','court','hearing']):
            domain = "civil_procedure"
        else:
            domain = "general_law"

        return {
            "legal_entities":list (set (entities)) [:10],
            "procedures":["legal procedure","administrative process"],
            "requirements":["legal compliance","procedural requirements"],
            "key_concepts":["government","legislation","law"],
            "legal_domain":domain,
            "complexity_score":min (len (content)//200 + 3,10)
            }

    def generate_instruction_data (self,section_num: str,title: str,content: str) -> List [Dict [str,str]]:
        """Generate instruction-response pairs using LLM"""
        prompt = f"""Create 3 instruction-response pairs for Ohio Revised Code Section {section_num} about {title}:

CONTENT: {content [:800]}

Generate 3 different instruction styles:
1. Explanation request
2. Summary request  
3. Practical application request

Format as JSON array:
[
  {{"instruction": "...", "response": "..."}},
  {{"instruction": "...", "response": "..."}},
  {{"instruction": "...", "response": "..."}}
]

Make responses comprehensive and educational."""

        try:
            response = self.generate_response (prompt,500)
            response = self.clean_json_response (response)

            if response.startswith ('['):
                # Handle array response
                start = response.find ('[')
                end = response.rfind (']')
                if start != -1 and end != -1:
                    response = response [start:end + 1]
                return json.loads (response)

        except Exception as e:
            print (f"   ⚠️ Error generating instruction data: {e}")

        # Fallback instruction data
        return [
            {
                "instruction":f"Explain Ohio Revised Code Section {section_num}.",
                "response":f"Ohio Revised Code Section {section_num} addresses {title.lower ()}. {content [:300]}..."
                },
            {
                "instruction":f"What does Section {section_num} require?",
                "response":f"Section {section_num} establishes requirements for {title.lower ()} including the procedures and obligations outlined in the statute."
                },
            {
                "instruction":f"How does Section {section_num} apply in practice?",
                "response":f"In practice, Section {section_num} governs {title.lower ()} by establishing the legal framework and procedural requirements."
                }
            ]

    def generate_qa_pairs (self,section_num: str,title: str,content: str) -> List [Dict [str,str]]:
        """Generate Q&A pairs using LLM"""
        prompt = f"""Create 4 question-answer pairs for Ohio Revised Code Section {section_num}:

TITLE: {title}
CONTENT: {content [:600]}

Generate questions of different types:
1. Basic comprehension ("What does this section establish?")
2. Specific detail ("Who is responsible for...?")
3. Requirements ("What are the requirements under...?")
4. Application ("How does this apply when...?")

Format as JSON array:
[
  {{"question": "...", "answer": "...", "type": "comprehension"}},
  {{"question": "...", "answer": "...", "type": "detail"}},
  {{"question": "...", "answer": "...", "type": "requirement"}},
  {{"question": "...", "answer": "...", "type": "application"}}
]"""

        try:
            response = self.generate_response (prompt,600)
            if response.startswith ('['):
                start = response.find ('[')
                end = response.rfind (']')
                if start != -1 and end != -1:
                    response = response [start:end + 1]
                return json.loads (response)

        except Exception as e:
            print (f"   ⚠️ Error generating Q&A pairs: {e}")

        # Fallback Q&A pairs
        return [
            {
                "question":f"What does Ohio Revised Code Section {section_num} establish?",
                "answer":content,
                "type":"comprehension"
                }
            ]

    def generate_analysis_data (self,section_num: str,title: str,content: str) -> Dict [str,Any]:
        """Generate legal analysis using LLM"""
        prompt = f"""Provide legal analysis for Ohio Revised Code Section {section_num}:

TITLE: {title}
CONTENT: {content [:700]}

Analyze and return JSON with:
- legal_framework: Brief description of what this establishes
- key_provisions: Array of 3-5 main provisions
- implications: What this means in practice
- related_concepts: Array of related legal concepts
- practical_application: How this would be applied

Return only valid JSON."""

        try:
            response = self.generate_response (prompt,400)
            response = self.clean_json_response (response)
            return json.loads (response)

        except Exception as e:
            print (f"   ⚠️ Error generating analysis: {e}")

        # Fallback analysis
        return {
            "legal_framework":f"Section {section_num} addresses {title.lower ()}.",
            "key_provisions":[f"Section {section_num} provisions",title,"Legal requirements"],
            "implications":"Establishes legal requirements and procedures",
            "related_concepts":["government","legislation","procedure"],
            "practical_application":f"Applies to {title.lower ()} in government operations."
            }

    def process_single_document (self,raw_item: Dict [str,Any]) -> Optional [Dict [str,Any]]:
        """Process a single document from your data format"""
        try:
            # Extract from your actual data structure
            header = raw_item.get ('header','')
            paragraphs = raw_item.get ('paragraphs',[])

            # Combine paragraphs into content
            content = self.combine_paragraphs (paragraphs)

            # Skip if content too short
            if len (content) < 50:
                return None

            # Extract section info from header
            section_number,title = self.extract_section_info (header)

            print (f"   📄 Processing Section {section_number}: {title [:50]}...")

            # Use LLM for intelligent analysis
            legal_analysis = self.extract_legal_concepts_with_llm (content)
            instruction_data = self.generate_instruction_data (section_number,title,content)
            qa_pairs = self.generate_qa_pairs (section_number,title,content)
            analysis_data = self.generate_analysis_data (section_number,title,content)

            return {
                'original':raw_item,
                'section_number':section_number,
                'section_title':title,
                'content':content,
                'url':'',  # Your data doesn't have URLs
                'url_hash':'',  # Your data doesn't have URL hashes
                'legal_analysis':legal_analysis,
                'instruction_data':instruction_data,
                'qa_pairs':qa_pairs,
                'analysis_data':analysis_data
                }

        except Exception as e:
            print (f"   ❌ Error processing document: {e}")
            return None

    def process_dataset (self,input_data: List [Dict [str,Any]]) -> List [Dict [str,Any]]:
        """Process entire dataset"""
        print (f"📊 Processing {len (input_data)} documents...")

        enriched_data = []
        for i,item in enumerate (input_data,1):
            print (f"🔄 Processing {i}/{len (input_data)}")

            enriched = self.process_single_document (item)
            if enriched:
                enriched_data.append (enriched)

            # Progress update every 50 items
            if i%50 == 0:
                print (f"   ✅ Successfully processed {len (enriched_data)} documents")

        return enriched_datad_data

    def save_training_datasets (self,enriched_data: List [Dict [str,Any]],output_base: str = "ohio_legal"):
        """Save multiple training format files"""
        timestamp = datetime.now ().strftime ("%Y%m%d_%H%M%S")
        output_dir = Path ("training_datasets")
        output_dir.mkdir (exist_ok=True)

        print ("💾 Generating training datasets...")

        # 1. Basic JSONL format (header + paragraphs)
        basic_data = []
        for item in enriched_data:
            basic_data.append (
                {
                    "header":item ['original'] ['header'],
                    "paragraphs":item ['content']
                    }
                )

        with open (output_dir/f"{output_base}_basic_{timestamp}.jsonl",'w',encoding='utf-8') as f:
            for item in basic_data:
                f.write (json.dumps (item,ensure_ascii=False) + '\n')

        # 2. Chat training format
        chat_data = []
        for item in enriched_data:
            for inst in item ['instruction_data']:
                chat_data.append (
                    {
                        "messages":[
                            {"role":"user","content":inst ['instruction']},
                            {"role":"assistant","content":inst ['response']}
                            ],
                        "metadata":{
                            "section":item ['section_number'],
                            "domain":item ['legal_analysis'] ['legal_domain']
                            }
                        }
                    )

        with open (output_dir/f"{output_base}_chat_{timestamp}.jsonl",'w',encoding='utf-8') as f:
            for item in chat_data:
                f.write (json.dumps (item,ensure_ascii=False) + '\n')

        # 3. Q&A format
        qa_data = []
        for item in enriched_data:
            for qa in item ['qa_pairs']:
                qa_data.append (
                    {
                        "question":qa ['question'],
                        "answer":qa ['answer'],
                        "type":qa ['type'],
                        "context":item ['content'],
                        "source_section":item ['section_number'],
                        "metadata":{
                            "domain":item ['legal_analysis'] ['legal_domain'],
                            "complexity":item ['legal_analysis'] ['complexity_score']
                            }
                        }
                    )

        with open (output_dir/f"{output_base}_qa_{timestamp}.jsonl",'w',encoding='utf-8') as f:
            for item in qa_data:
                f.write (json.dumps (item,ensure_ascii=False) + '\n')

        # 4. Instruction format
        instruction_data = []
        for item in enriched_data:
            for inst in item ['instruction_data']:
                instruction_data.append (
                    {
                        "instruction":inst ['instruction'],
                        "input":"",
                        "output":inst ['response'],
                        "metadata":{
                            "section":item ['section_number'],
                            "title":item ['section_title'],
                            "domain":item ['legal_analysis'] ['legal_domain'],
                            "complexity":item ['legal_analysis'] ['complexity_score']
                            }
                        }
                    )

        with open (output_dir/f"{output_base}_instructions_{timestamp}.jsonl",'w',encoding='utf-8') as f:
            for item in instruction_data:
                f.write (json.dumps (item,ensure_ascii=False) + '\n')

        # 5. Full enriched format
        with open (output_dir/f"{output_base}_enriched_{timestamp}.jsonl",'w',encoding='utf-8') as f:
            for item in enriched_data:
                f.write (json.dumps (item,ensure_ascii=False) + '\n')

        print (f"✅ Generated {len (enriched_data)} enriched examples!")
        print (f"📂 Files saved with timestamp: {timestamp}")
        print (f"   📝 Basic JSONL: {len (basic_data)} examples")
        print (f"   💬 Chat: {len (chat_data)} examples")
        print (f"   ❓ Q&A: {len (qa_data)} examples")
        print (f"   📚 Instructions: {len (instruction_data)} examples")
        print (f"   📊 Enriched: {len (enriched_data)} examples")


def main ():
    """Main processing function"""
    # Configuration - EDIT THESE PATHS
    INPUT_FILE = "/Users/justinrussell/lawscraper/revised-code/training_datasets/output_sorted.jsonl"  # Your JSONL file
    MODEL_PATH = "/Users/justinrussell/mistral7b"  # Your GGUF model path
    OUTPUT_BASE = "ohio_legal"

    print ("🚀 Starting Legal Data Processing...")
    print (f"📁 Input: {INPUT_FILE}")
    print (f"🤖 Model: {MODEL_PATH}")

    # Validate files exist
    if not Path (INPUT_FILE).exists ():
        print (f"❌ Error: Input file not found: {INPUT_FILE}")
        print ("   Please update INPUT_FILE path in the script")
        return

    if not Path (MODEL_PATH).exists ():
        print (f"❌ Error: Model file not found: {MODEL_PATH}")
        print ("   Please update MODEL_PATH in the script")
        return

    try:
        # Load JSON data (single JSON array or object)
        with open (INPUT_FILE,'r',encoding='utf-8') as f:
            raw_data = json.load (f)

        # Handle different JSON structures
        if isinstance (raw_data,list):
            # It's already a list of documents
            print (f"📊 Loaded {len (raw_data)} documents from JSON array")
        elif isinstance (raw_data,dict):
            # It's a single document, wrap in list
            raw_data = [raw_data]
            print (f"📊 Loaded 1 document from JSON object")
        else:
            print (f"❌ Unexpected JSON structure: {type (raw_data)}")
            return

        # Initialize processor with LLM
        processor = LegalDataProcessor (MODEL_PATH)

        # Process the data
        enriched_data = processor.process_dataset (raw_data)

        # Save all training formats
        processor.save_training_datasets (enriched_data,OUTPUT_BASE)

        print ("\n🎉 Processing complete!")
        print ("\n📂 Generated files in training_datasets/:")
        print ("   • basic.jsonl - Simple header + paragraphs format")
        print ("   • chat.jsonl - Conversational training data")
        print ("   • qa.jsonl - Question-answer pairs")
        print ("   • instructions.jsonl - Instruction-following data")
        print ("   • enriched.jsonl - Complete analysis dataset")

    except Exception as e:
        print (f"❌ Error: {e}")
        print ("   Check your input file format and model path")


if __name__ == "__main__":
    main ()