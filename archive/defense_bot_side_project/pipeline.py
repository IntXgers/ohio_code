#!/usr/bin/env python3
"""
Defense Attorney Bot - Fine-Tuning Pipeline
Fine-tunes models on defense-focused legal data
Supports multiple training frameworks
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import torch
from datasets import Dataset, load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
    BitsAndBytesConfig
)
from peft import (
    LoraConfig,
    get_peft_model,
    prepare_model_for_kbit_training,
    TaskType
)
import numpy as np
from datetime import datetime
import wandb
import fire
import yaml
from tqdm import tqdm

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DefenseDatasetBuilder:
    """Build and prepare datasets for defense attorney training"""

    SYSTEM_PROMPT = """You are an experienced criminal defense attorney specializing in Ohio law. Your role is to:
- Zealously advocate for your client's rights and interests
- Identify weaknesses in the prosecution's case
- Develop creative defense strategies
- Protect constitutional rights
- Provide strategic legal advice

Always think from a defense perspective, looking for reasonable doubt, procedural errors, and alternative explanations."""

    def __init__(self, tokenizer, max_length: int = 2048):
        self.tokenizer = tokenizer
        self.max_length = max_length

    def load_jsonl_files(self, file_paths: List[str]) -> List[Dict]:
        """Load multiple JSONL files"""
        all_data = []
        for path in file_paths:
            logger.info(f"Loading {path}")
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    all_data.append(json.loads(line.strip()))
        logger.info(f"Loaded {len(all_data)} total examples")
        return all_data

    def format_for_training(self, example: Dict) -> str:
        """Format example for training based on type"""

        # ChatML format (for conversational data)
        if 'messages' in example:
            formatted = ""
            for message in example['messages']:
                role = message['role']
                content = message['content']

                if role == 'system':
                    formatted += f"<|system|>\n{content}\n"
                elif role == 'user':
                    formatted += f"<|user|>\n{content}\n"
                elif role == 'assistant':
                    formatted += f"<|assistant|>\n{content}\n"

            # Add end token
            formatted += "<|endoftext|>"
            return formatted

        # Instruction format
        elif 'instruction' in example and 'response' in example:
            instruction = example['instruction']
            response = example['response']

            formatted = f"""<|system|>
{self.SYSTEM_PROMPT}
<|user|>
{instruction}
<|assistant|>
{response}
<|endoftext|>"""
            return formatted

        # Q&A format
        elif 'question' in example and 'answer' in example:
            question = example['question']
            answer = example['answer']

            formatted = f"""<|system|>
{self.SYSTEM_PROMPT}
<|user|>
{question}
<|assistant|>
{answer}
<|endoftext|>"""
            return formatted

        else:
            raise ValueError(f"Unknown example format: {example.keys()}")

    def tokenize_function(self, examples):
        """Tokenize examples for training"""
        # Format each example
        formatted_texts = [self.format_for_training(ex) for ex in examples['data']]

        # Tokenize
        tokenized = self.tokenizer(
            formatted_texts,
            truncation=True,
            padding='max_length',
            max_length=self.max_length,
            return_tensors=None
        )

        # Set labels (same as input_ids for causal LM)
        tokenized['labels'] = tokenized['input_ids'].copy()

        return tokenized

    def prepare_dataset(self, data: List[Dict], split: str = 'train') -> Dataset:
        """Prepare dataset for training"""
        # Create dataset
        dataset = Dataset.from_dict({'data': data})

        # Tokenize
        tokenized_dataset = dataset.map(
            self.tokenize_function,
            batched=True,
            remove_columns=['data'],
            desc=f"Tokenizing {split} dataset"
        )

        return tokenized_dataset


class DefenseFineTuner:
    """Fine-tune models for defense attorney tasks"""

    def __init__(self, config: Dict):
        self.config = config
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"Using device: {self.device}")

        # Initialize wandb if configured
        if config.get('use_wandb', False):
            wandb.init(
                project=config.get('wandb_project', 'defense-attorney-bot'),
                name=config.get('run_name', f'defense-finetune-{datetime.now().strftime("%Y%m%d-%H%M%S")}'),
                config=config
            )

    def load_model_and_tokenizer(self):
        """Load base model and tokenizer"""
        model_name = self.config['model_name']
        logger.info(f"Loading model: {model_name}")

        # Quantization config for large models
        if self.config.get('use_quantization', True):
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16,
                bnb_4bit_use_double_quant=True
            )
        else:
            bnb_config = None

        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            trust_remote_code=True,
            padding_side='left'  # Important for batch generation
        )

        # Add special tokens if needed
        special_tokens = {
            "pad_token": "<|pad|>",
            "eos_token": "<|endoftext|>",
            "additional_special_tokens": ["<|system|>", "<|user|>", "<|assistant|>"]
        }

        smart_tokenizer_and_embedding_resize(
            special_tokens,
            self.tokenizer,
            None  # Will be set after model loads
        )

        # Load model
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True,
            torch_dtype=torch.bfloat16
        )

        # Resize embeddings after loading model
        self.model.resize_token_embeddings(len(self.tokenizer))

        # Prepare for k-bit training if using quantization
        if self.config.get('use_quantization', True):
            self.model = prepare_model_for_kbit_training(self.model)

        # Configure LoRA
        lora_config = LoraConfig(
            r=self.config.get('lora_r', 16),
            lora_alpha=self.config.get('lora_alpha', 32),
            target_modules=self.config.get('target_modules', ["q_proj", "v_proj", "k_proj", "o_proj"]),
            lora_dropout=self.config.get('lora_dropout', 0.1),
            bias="none",
            task_type=TaskType.CAUSAL_LM
        )

        self.model = get_peft_model(self.model, lora_config)
        self.model.print_trainable_parameters()

        logger.info("Model and tokenizer loaded successfully")

    def create_training_args(self) -> TrainingArguments:
        """Create training arguments"""
        return TrainingArguments(
            output_dir=self.config['output_dir'],
            num_train_epochs=self.config.get('num_epochs', 3),
            per_device_train_batch_size=self.config.get('batch_size', 4),
            per_device_eval_batch_size=self.config.get('batch_size', 4),
            gradient_accumulation_steps=self.config.get('gradient_accumulation_steps', 4),
            warmup_steps=self.config.get('warmup_steps', 100),
            learning_rate=self.config.get('learning_rate', 2e-4),
            fp16=True,
            logging_steps=10,
            save_steps=self.config.get('save_steps', 500),
            eval_steps=self.config.get('eval_steps', 500),
            evaluation_strategy="steps",
            save_strategy="steps",
            load_best_model_at_end=True,
            report_to="wandb" if self.config.get('use_wandb', False) else "none",
            run_name=self.config.get('run_name', 'defense-finetune'),
            gradient_checkpointing=self.config.get('gradient_checkpointing', True),
            optim=self.config.get('optimizer', 'paged_adamw_8bit'),
            weight_decay=self.config.get('weight_decay', 0.01),
            max_grad_norm=self.config.get('max_grad_norm', 0.3),
            push_to_hub=False,
            remove_unused_columns=False
        )

    def train(self, train_dataset: Dataset, eval_dataset: Optional[Dataset] = None):
        """Train the model"""
        # Create data collator
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False  # Causal LM
        )

        # Create training arguments
        training_args = self.create_training_args()

        # Create trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            data_collator=data_collator,
            callbacks=[DefenseMetricsCallback()]  # Custom callback for defense-specific metrics
        )

        # Train
        logger.info("Starting training...")
        trainer.train()

        # Save the final model
        logger.info("Saving final model...")
        trainer.save_model()
        self.tokenizer.save_pretrained(self.config['output_dir'])

        # Save training config
        with open(Path(self.config['output_dir']) / 'training_config.yaml', 'w') as f:
            yaml.dump(self.config, f)

        logger.info(f"Training complete! Model saved to {self.config['output_dir']}")


class DefenseMetricsCallback:
    """Custom callback to track defense-specific metrics during training"""

    def on_log(self, args, state, control, logs=None, **kwargs):
        """Log custom metrics"""
        if logs:
            # Add custom metrics here if needed
            pass


def smart_tokenizer_and_embedding_resize(
        special_tokens: Dict,
        tokenizer: AutoTokenizer,
        model: Optional[AutoModelForCausalLM]
):
    """Resize tokenizer and embedding"""
    num_new_tokens = tokenizer.add_special_tokens(special_tokens)

    if model is not None and num_new_tokens > 0:
        model.resize_token_embeddings(len(tokenizer))
        input_embeddings = model.get_input_embeddings().weight.data
        output_embeddings = model.get_output_embeddings().weight.data

        # Initialize new embeddings
        input_embeddings_avg = input_embeddings[:-num_new_tokens].mean(dim=0, keepdim=True)
        output_embeddings_avg = output_embeddings[:-num_new_tokens].mean(dim=0, keepdim=True)

        input_embeddings[-num_new_tokens:] = input_embeddings_avg
        output_embeddings[-num_new_tokens:] = output_embeddings_avg


def create_train_eval_split(data: List[Dict], eval_ratio: float = 0.1) -> Tuple[List[Dict], List[Dict]]:
    """Split data into train and eval sets"""
    np.random.shuffle(data)
    split_idx = int(len(data) * (1 - eval_ratio))
    return data[:split_idx], data[split_idx:]


def main(
        config_file: str = None,
        model_name: str = "mistralai/Mistral-7B-Instruct-v0.2",
        data_dir: str = "data/enriched/stage_1_statutory",
        output_dir: str = "models/defense-attorney-v1",
        num_epochs: int = 3,
        batch_size: int = 4,
        learning_rate: float = 2e-4,
        use_wandb: bool = False
):
    """
    Main training function

    Args:
        config_file: Path to YAML config file (overrides other args)
        model_name: Base model to fine-tune
        data_dir: Directory containing training JSONL files
        output_dir: Where to save the fine-tuned model
        num_epochs: Number of training epochs
        batch_size: Training batch size
        learning_rate: Learning rate
        use_wandb: Whether to use Weights & Biases logging
    """

    # Load config
    if config_file and Path(config_file).exists():
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
    else:
        config = {
            'model_name': model_name,
            'data_dir': data_dir,
            'output_dir': output_dir,
            'num_epochs': num_epochs,
            'batch_size': batch_size,
            'learning_rate': learning_rate,
            'use_wandb': use_wandb,
            'use_quantization': True,
            'lora_r': 16,
            'lora_alpha': 32,
            'lora_dropout': 0.1,
            'target_modules': ["q_proj", "v_proj", "k_proj", "o_proj"],
            'gradient_accumulation_steps': 4,
            'warmup_steps': 100,
            'save_steps': 500,
            'eval_steps': 500,
            'max_length': 2048,
            'gradient_checkpointing': True,
            'optimizer': 'paged_adamw_8bit'
        }

    # Initialize fine-tuner
    fine_tuner = DefenseFineTuner(config)
    fine_tuner.load_model_and_tokenizer()

    # Load data
    data_dir = Path(config['data_dir'])
    jsonl_files = list(data_dir.glob("*.jsonl"))
    logger.info(f"Found {len(jsonl_files)} JSONL files in {data_dir}")

    # Build dataset
    dataset_builder = DefenseDatasetBuilder(
        fine_tuner.tokenizer,
        max_length=config.get('max_length', 2048)
    )

    # Load all data
    all_data = dataset_builder.load_jsonl_files([str(f) for f in jsonl_files])

    # Create train/eval split
    train_data, eval_data = create_train_eval_split(all_data)
    logger.info(f"Train examples: {len(train_data)}, Eval examples: {len(eval_data)}")

    # Prepare datasets
    train_dataset = dataset_builder.prepare_dataset(train_data, 'train')
    eval_dataset = dataset_builder.prepare_dataset(eval_data, 'eval')

    # Train
    fine_tuner.train(train_dataset, eval_dataset)

    # Test the model
    logger.info("\n🧪 Testing the fine-tuned model...")
    test_prompts = [
        "I've been charged with OVI in Ohio. What defenses should I consider?",
        "The police searched my car without consent. How can I challenge this?",
        "What constitutional issues exist with Ohio's drug possession laws?"
    ]

    for prompt in test_prompts:
        logger.info(f"\nPrompt: {prompt}")
        # Here you would generate a response - implementation depends on your setup
        logger.info("(Response generation would go here)")


if __name__ == "__main__":
    fire.Fire(main)