# core/model_manager.py
import lmdb
from llama_cpp import Llama
import yaml
from pathlib import Path
import json
import logging


class ModelManager:
    """Singleton model and LMDB manager"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self):
        if not self.initialized:
            with open('core/config.yaml', 'r') as f:
                self.config = yaml.safe_load(f)
            self.model = None
            self.lmdb_env = None
            self.citation_map = None
            self.initialized = True

    def load_model(self):
        if not self.model:
            self.model = Llama(
                model_path=self.config['model']['path'],
                n_ctx=self.config['model']['context_size'],
                n_threads=self.config['model']['threads'],
                n_gpu_layers=-1
            )
        return self.model

    def load_lmdb(self):
        if not self.lmdb_env:
            self.lmdb_env = lmdb.open(
                self.config['lmdb']['path'],
                map_size=self.config['lmdb']['size']
            )
        return self.lmdb_env

    def load_citation_map(self):
        if not self.citation_map:
            with open(self.config['citation']['map_path'], 'r') as f:
                self.citation_map = json.load(f)
        return self.citation_map