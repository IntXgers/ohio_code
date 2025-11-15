#!/bin/bash
# setup_ohio_legal_platform.sh

echo "Setting up Ohio Legal Platform directory structure..."

# Root directory
ROOT_DIR="legal_doc_platform"
mkdir -p $ROOT_DIR
cd $ROOT_DIR

# Create root directories
mkdir -p services data infra models web utils

# ==================== SERVICES ====================
echo "Creating microservices structure..."

# Ohio Code Service
mkdir -p services/ohio_code_service/src/ohio_code_service
cat > services/ohio_code_service/src/ohio_code_service/__init__.py << 'EOF'
"""Ohio Revised Code lookup service"""
__version__ = "0.1.0"
EOF

cat > services/ohio_code_service/src/ohio_code_service/main.py << 'EOF'
from fastapi import FastAPI, HTTPException
from typing import Optional
import lmdb
import json

app = FastAPI(title="Ohio Code Service")

class OhioCodeStore:
    def __init__(self):
        self.env = lmdb.open('/data/ohio_code.lmdb', readonly=True)
    
    def get_statute(self, section: str) -> Optional[dict]:
        with self.env.begin() as txn:
            data = txn.get(section.encode())
            if data:
                return json.loads(data)
        return None

store = OhioCodeStore()

@app.get("/api/v1/statute/{section}")
async def get_statute(section: str):
    result = store.get_statute(section)
    if not result:
        raise HTTPException(status_code=404, detail=f"Section {section} not found")
    return result

@app.get("/health")
async def health():
    return {"status": "healthy"}
EOF

cat > services/ohio_code_service/src/ohio_code_service/lmdb_store.py << 'EOF'
import lmdb
import json
from pathlib import Path
from typing import Optional, Dict, List

class LMDBStore:
    def __init__(self, db_path: str):
        self.env = lmdb.open(db_path, map_size=10*1024*1024*1024)
    
    def put(self, key: str, value: dict) -> bool:
        with self.env.begin(write=True) as txn:
            return txn.put(key.encode(), json.dumps(value).encode())
    
    def get(self, key: str) -> Optional[dict]:
        with self.env.begin() as txn:
            data = txn.get(key.encode())
            if data:
                return json.loads(data)
        return None
    
    def get_range(self, start: str, end: str) -> List[dict]:
        results = []
        with self.env.begin() as txn:
            cursor = txn.cursor()
            cursor.set_range(start.encode())
            for key, value in cursor:
                if key.decode() > end:
                    break
                results.append(json.loads(value))
        return results
EOF

cat > services/ohio_code_service/src/ohio_code_service/citation_decoder.py << 'EOF'
def decode_ohio_code(citation):
    """
    Decode Ohio Revised Code citation
    Examples:
    - 317.01 = Title 3, Chapter 17, Section 01
    - 2903.01 = Title 29, Chapter 03, Section 01
    """
    parts = citation.split('.')
    if len(parts) != 2:
        return None

    prefix = parts[0]
    section = parts[1]

    if len(prefix) == 3:
        title = int(prefix[0])
        chapter = int(prefix[1:3])
    elif len(prefix) == 4:
        title = int(prefix[0:2])
        chapter = int(prefix[2:4])
    else:
        return None

    return {
        'title': title,
        'chapter': chapter,
        'section': section
    }
EOF

cat > services/ohio_code_service/Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install -e .

EXPOSE 8000

CMD ["uvicorn", "ohio_code_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

# Citation Graph Service
mkdir -p services/citation_graph_service/src/citation_graph_service
cat > services/citation_graph_service/src/citation_graph_service/__init__.py << 'EOF'
"""Citation graph analysis service"""
__version__ = "0.1.0"
EOF

cat > services/citation_graph_service/src/citation_graph_service/main.py << 'EOF'
from fastapi import FastAPI
import networkx as nx
import pickle
import json
from pathlib import Path

app = FastAPI(title="Citation Graph Service")

class CitationGraph:
    def __init__(self):
        self.graph = self.load_graph()
    
    def load_graph(self):
        graph_path = Path('/data/citation_graph.pickle')
        if graph_path.exists():
            with open(graph_path, 'rb') as f:
                return pickle.load(f)
        return nx.DiGraph()
    
    def get_complexity(self, section: str):
        if section not in self.graph:
            return None
        return {
            'in_degree': self.graph.in_degree(section),
            'out_degree': self.graph.out_degree(section),
            'total_citations': self.graph.degree(section)
        }

graph_store = CitationGraph()

@app.get("/api/v1/citation/{section}/complexity")
async def get_complexity(section: str):
    return graph_store.get_complexity(section)

@app.get("/api/v1/citation/{section}/related")
async def get_related(section: str):
    if section not in graph_store.graph:
        return {"error": "Section not found"}
    return {
        "cites": list(graph_store.graph.successors(section)),
        "cited_by": list(graph_store.graph.predecessors(section))
    }
EOF

cat > services/citation_graph_service/src/citation_graph_service/graph_builder.py << 'EOF'
import networkx as nx
import json
from pathlib import Path
from typing import Dict, List

class GraphBuilder:
    def __init__(self):
        self.graph = nx.DiGraph()
    
    def build_from_citation_map(self, citation_map: Dict[str, List[str]]):
        for source, targets in citation_map.items():
            for target in targets:
                self.graph.add_edge(source, target)
        return self.graph
    
    def analyze_complexity(self):
        return {
            'nodes': self.graph.number_of_nodes(),
            'edges': self.graph.number_of_edges(),
            'strongly_connected': nx.number_strongly_connected_components(self.graph)
        }
EOF

cat > services/citation_graph_service/Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install -e .

EXPOSE 8000

CMD ["uvicorn", "citation_graph_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

# Document Assembly Service
mkdir -p services/document_assembly_service/src/document_assembly_service/{agents,templates}
cat > services/document_assembly_service/src/document_assembly_service/__init__.py << 'EOF'
"""Document assembly and generation service"""
__version__ = "0.1.0"
EOF

cat > services/document_assembly_service/src/document_assembly_service/main.py << 'EOF'
from fastapi import FastAPI
from typing import Dict
import httpx

app = FastAPI(title="Document Assembly Service")

class DocumentAssembly:
    def __init__(self):
        self.ohio_code_url = "http://ohio-code-service:8000"
        self.citation_url = "http://citation-graph-service:8000"
        self.llm_url = "http://llm-inference-service:8000"
    
    async def generate_llc_package(self, company_info: Dict):
        # Implementation here
        pass

assembly = DocumentAssembly()

@app.post("/api/v1/llc/create")
async def create_llc(company_info: Dict):
    return await assembly.generate_llc_package(company_info)

@app.post("/api/v1/operating-agreement/generate")
async def generate_operating_agreement(llc_info: Dict):
    return {"status": "generating", "llc_info": llc_info}
EOF

cat > services/document_assembly_service/src/document_assembly_service/agents/__init__.py << 'EOF'
from .llc_formation import LLCFormationAgent
from .operating_agreement import OperatingAgreementAgent
from .compliance_checker import ComplianceAgent

__all__ = ['LLCFormationAgent', 'OperatingAgreementAgent', 'ComplianceAgent']
EOF

cat > services/document_assembly_service/src/document_assembly_service/agents/llc_formation.py << 'EOF'
import httpx
from typing import Dict

class LLCFormationAgent:
    def __init__(self):
        self.ohio_code_url = "http://ohio-code-service:8000"
        self.required_statutes = [
            "1706.01",  # Definitions
            "1706.16",  # Articles of Organization
            "1706.09"   # Statutory Agent
        ]
    
    async def generate_articles(self, company_info: Dict):
        # Fetch relevant statutes
        statutes = {}
        async with httpx.AsyncClient() as client:
            for statute in self.required_statutes:
                response = await client.get(f"{self.ohio_code_url}/api/v1/statute/{statute}")
                statutes[statute] = response.json()
        
        # Generate based on requirements
        return self.assemble_articles(company_info, statutes)
    
    def assemble_articles(self, info: Dict, statutes: Dict):
        return {
            "name": info.get("name"),
            "statutory_agent": info.get("agent"),
            "purpose": "Any lawful purpose under Ohio Rev Code 1706",
            "duration": "Perpetual"
        }
EOF

cat > services/document_assembly_service/src/document_assembly_service/agents/operating_agreement.py << 'EOF'
from typing import Dict, List

class OperatingAgreementAgent:
    def __init__(self):
        self.agreement_sections = [
            "1706.081",  # Operating agreement scope
            "1706.31",   # Member voting
            "1706.41",   # Distributions
            "1706.61"    # Dissolution
        ]
    
    async def generate_agreement(self, llc_info: Dict):
        if llc_info.get("member_count", 1) == 1:
            return await self.single_member_agreement(llc_info)
        else:
            return await self.multi_member_agreement(llc_info)
    
    async def single_member_agreement(self, info: Dict):
        return {
            "type": "single_member",
            "member": info.get("members", [{}])[0],
            "management": "member-managed"
        }
    
    async def multi_member_agreement(self, info: Dict):
        return {
            "type": "multi_member",
            "members": info.get("members", []),
            "voting": "per capita",
            "management": info.get("management", "member-managed")
        }
EOF

cat > services/document_assembly_service/src/document_assembly_service/agents/compliance_checker.py << 'EOF'
from typing import Dict, List

class ComplianceAgent:
    def __init__(self):
        self.citation_graph_url = "http://citation-graph-service:8000"
    
    async def check_compliance(self, document: str) -> Dict:
        # Extract citations from document
        citations = self.extract_citations(document)
        
        # Verify each citation
        issues = []
        for citation in citations:
            if not await self.verify_citation(citation):
                issues.append(f"Invalid citation: {citation}")
        
        return {
            "compliant": len(issues) == 0,
            "issues": issues
        }
    
    def extract_citations(self, document: str) -> List[str]:
        # Regex to find Ohio Rev Code citations
        import re
        pattern = r'\b\d{4}\.\d{2}\b'
        return re.findall(pattern, document)
    
    async def verify_citation(self, citation: str) -> bool:
        # Verify citation exists
        return True  # Placeholder
EOF

# LLM Inference Service
mkdir -p services/llm_inference_service/src/llm_inference_service
cat > services/llm_inference_service/src/llm_inference_service/__init__.py << 'EOF'
"""LLM inference service for legal text generation"""
__version__ = "0.1.0"
EOF

cat > services/llm_inference_service/src/llm_inference_service/main.py << 'EOF'
from fastapi import FastAPI
from typing import Dict
from llama_cpp import Llama

app = FastAPI(title="LLM Inference Service")

class ModelServer:
    def __init__(self):
        self.model = None  # Load on startup
    
    def load_model(self):
        self.model = Llama(
            model_path="/models/llama-3.1-8b-q8.gguf",
            n_ctx=8192,
            n_threads=8
        )
    
    async def generate(self, prompt: str, max_tokens: int = 2000):
        if not self.model:
            self.load_model()
        
        response = self.model(prompt, max_tokens=max_tokens)
        return response['choices'][0]['text']

model_server = ModelServer()

@app.post("/api/v1/generate")
async def generate(request: Dict):
    prompt = request.get("prompt")
    max_tokens = request.get("max_tokens", 2000)
    response = await model_server.generate(prompt, max_tokens)
    return {"text": response}
EOF

# Compliance Monitor Service
mkdir -p services/compliance_monitor_service/src/compliance_monitor_service
cat > services/compliance_monitor_service/src/compliance_monitor_service/__init__.py << 'EOF'
"""Compliance monitoring and subscription service"""
__version__ = "0.1.0"
EOF

cat > services/compliance_monitor_service/src/compliance_monitor_service/main.py << 'EOF'
from fastapi import FastAPI
from typing import Dict, List
import asyncio

app = FastAPI(title="Compliance Monitor Service")

class ComplianceMonitor:
    def __init__(self):
        self.subscriptions = {}
    
    async def monitor_changes(self, customer_id: str, statutes: List[str]):
        # Monitor specific statutes for changes
        pass
    
    async def check_updates(self):
        # Check for law updates
        pass

monitor = ComplianceMonitor()

@app.post("/api/v1/compliance/subscribe")
async def subscribe(subscription: Dict):
    return {"status": "subscribed", "id": subscription.get("customer_id")}

@app.get("/api/v1/compliance/updates/{customer_id}")
async def get_updates(customer_id: str):
    return {"updates": []}
EOF

# API Gateway Service
mkdir -p services/api_gateway_service/src/api_gateway_service/routes
cat > services/api_gateway_service/src/api_gateway_service/__init__.py << 'EOF'
"""API Gateway for Ohio Legal Platform"""
__version__ = "0.1.0"
EOF

cat > services/api_gateway_service/src/api_gateway_service/main.py << 'EOF'
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx

app = FastAPI(title="Ohio Legal Platform API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Ohio Legal Platform API v1.0"}

@app.post("/api/v1/llc/create")
async def create_llc(company_info: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://document-assembly-service:8000/api/v1/llc/create",
            json=company_info
        )
    return response.json()
EOF

# ==================== INFRASTRUCTURE ====================
echo "Creating Kubernetes infrastructure..."

# K3s namespace
cat > infra/namespace.yaml << 'EOF'
apiVersion: v1
kind: Namespace
metadata:
  name: ohio-legal
EOF

# Persistent Volumes
cat > infra/persistent-volumes.yaml << 'EOF'
apiVersion: v1
kind: PersistentVolume
metadata:
  name: ohio-data-pv
spec:
  capacity:
    storage: 10Gi
  accessModes:
    - ReadOnlyMany
  hostPath:
    path: /data/ohio-legal
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: ohio-data-pvc
  namespace: ohio-legal
spec:
  accessModes:
    - ReadOnlyMany
  resources:
    requests:
      storage: 10Gi
EOF

# Service deployments
mkdir -p infra/services/{ohio-code,citation-graph,document-assembly,llm-inference,compliance-monitor,api-gateway}

# Ohio Code Service Deployment
cat > infra/services/ohio-code/deployment.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ohio-code-service
  namespace: ohio-legal
spec:
  replicas: 2
  selector:
    matchLabels:
      app: ohio-code-service
  template:
    metadata:
      labels:
        app: ohio-code-service
    spec:
      containers:
      - name: ohio-code
        image: ohio-legal/ohio-code-service:latest
        ports:
        - containerPort: 8000
        volumeMounts:
        - name: ohio-data
          mountPath: /data
          readOnly: true
      volumes:
      - name: ohio-data
        persistentVolumeClaim:
          claimName: ohio-data-pvc
EOF

cat > infra/services/ohio-code/service.yaml << 'EOF'
apiVersion: v1
kind: Service
metadata:
  name: ohio-code-service
  namespace: ohio-legal
spec:
  selector:
    app: ohio-code-service
  ports:
  - port: 8000
    targetPort: 8000
EOF

# Citation Graph Service Deployment
cat > infra/services/citation-graph/deployment.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: citation-graph-service
  namespace: ohio-legal
spec:
  replicas: 2
  selector:
    matchLabels:
      app: citation-graph-service
  template:
    metadata:
      labels:
        app: citation-graph-service
    spec:
      containers:
      - name: citation-graph
        image: ohio-legal/citation-graph-service:latest
        ports:
        - containerPort: 8000
        volumeMounts:
        - name: ohio-data
          mountPath: /data
          readOnly: true
      volumes:
      - name: ohio-data
        persistentVolumeClaim:
          claimName: ohio-data-pvc
EOF

cat > infra/services/citation-graph/service.yaml << 'EOF'
apiVersion: v1
kind: Service
metadata:
  name: citation-graph-service
  namespace: ohio-legal
spec:
  selector:
    app: citation-graph-service
  ports:
  - port: 8000
    targetPort: 8000
EOF

# Enrichment Job
mkdir -p infra/jobs
cat > infra/jobs/enrichment-job.yaml << 'EOF'
apiVersion: batch/v1
kind: Job
metadata:
  name: enrichment-job
  namespace: ohio-legal
spec:
  template:
    spec:
      containers:
      - name: enrichment
        image: ohio-legal/enrichment:latest
        command: ["python", "-m", "enrichment.main"]
      restartPolicy: Never
  backoffLimit: 3
EOF

# Docker Compose for local development
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  ohio-code:
    build: ./services/ohio_code_service
    ports:
      - "8001:8000"
    volumes:
      - ./data:/data:ro
    networks:
      - ohio-legal

  citation-graph:
    build: ./services/citation_graph_service
    ports:
      - "8002:8000"
    volumes:
      - ./data:/data:ro
    networks:
      - ohio-legal

  document-assembly:
    build: ./services/document_assembly_service
    ports:
      - "8003:8000"
    networks:
      - ohio-legal
    depends_on:
      - ohio-code
      - citation-graph

  api-gateway:
    build: ./services/api_gateway_service
    ports:
      - "8000:8000"
    networks:
      - ohio-legal
    depends_on:
      - document-assembly

networks:
  ohio-legal:
    driver: bridge

volumes:
  ohio-data:
EOF

# Create data prep script
cat > prepare_data.py << 'EOF'
#!/usr/bin/env python3
"""Prepare LMDB databases from existing Ohio data"""

import lmdb
import json
import pickle
import networkx as nx
from pathlib import Path

def create_ohio_code_lmdb():
    """Convert JSONL to LMDB"""
    source = Path("ohio_revised/src/ohio_revised/ohio_revised_data/ohio_revised_code_complete/ohio_revised_code_complete.jsonl")
    target = Path("data/ohio_code.lmdb")
    
    env = lmdb.open(str(target), map_size=10*1024*1024*1024)
    
    with open(source) as f:
        with env.begin(write=True) as txn:
            for line in f:
                doc = json.loads(line)
                section = doc.get('section_number', '')
                if section:
                    txn.put(section.encode(), line.encode())
    
    print(f"Created {target}")

def create_citation_graph():
    """Create NetworkX graph from citation map"""
    source = Path("ohio_revised/src/ohio_revised/ohio_revised_data/citation_analysis/citation_map.json")
    target = Path("data/citation_graph.pickle")
    
    with open(source) as f:
        citation_map = json.load(f)
    
    G = nx.DiGraph()
    for source_section, targets in citation_map.items():
        for target in targets:
            G.add_edge(source_section, target)
    
    with open(target, 'wb') as f:
        pickle.dump(G, f)
    
    print(f"Created {target} with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")

if __name__ == "__main__":
    create_ohio_code_lmdb()
    create_citation_graph()
EOF

# Create utilities
mkdir -p utils/citation_utils/src/citation_utils
cat > utils/citation_utils/src/citation_utils/__init__.py << 'EOF'
"""Citation utilities shared across services"""
from .decoder import decode_ohio_code

__all__ = ['decode_ohio_code']
EOF

cat > utils/citation_utils/src/citation_utils/decoder.py << 'EOF'
def decode_ohio_code(citation):
    """
    Decode Ohio Revised Code citation
    Examples:
    - 317.01 = Title 3, Chapter 17, Section 01
    - 2903.01 = Title 29, Chapter 03, Section 01
    """
    parts = citation.split('.')
    if len(parts) != 2:
        return None

    prefix = parts[0]
    section = parts[1]

    if len(prefix) == 3:
        title = int(prefix[0])
        chapter = int(prefix[1:3])
    elif len(prefix) == 4:
        title = int(prefix[0:2])
        chapter = int(prefix[2:4])
    else:
        return None

    return {
        'title': title,
        'chapter': chapter,
        'section': section
    }
EOF

# Create README
cat > README.md << 'EOF'
# Ohio Legal Platform

AI-powered legal document generation for Ohio businesses.

## Setup

1. Initialize uv workspace:
```bash
uv init

for service in services/*/; do
    cd $service
    uv init
    cd ../..
done
EOF
