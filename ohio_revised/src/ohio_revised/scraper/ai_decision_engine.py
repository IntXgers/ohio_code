"""
AI Decision Engine

This module implements the AI Decision Engine component of the Smart Scraper system.
The AI Decision Engine is responsible for:
1. Making real-time decisions during the scraping process
2. Handling navigation choices based on content analysis
3. Responding to challenges (CAPTCHAs, login forms, etc.)
4. Determining extraction priorities for different data elements
5. Learning from past decisions to improve future performance

The engine uses a combination of rule-based heuristics and machine learning models
to make intelligent decisions that maximize the value of scraped data while
minimizing resource usage and avoiding detection.

The AI Decision Engine operates independently in its own container and communicates
exclusively through the event system, making it compatible with the event-driven
architecture requirements. It maintains its own model state and can continue to learn
and evolve from the training data that gets collected during scraping operations.

EXTENSION POINT: The decision engine can be extended with more sophisticated
AI models, reinforcement learning techniques, or specialized models for
specific e-commerce platforms.

Author: AI Assistant
Date: April 3, 2025
"""

import asyncio
import datetime
import json
import logging
import random
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import numpy as np
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field

# Import common interfaces and models
# In production, these would be imported from a shared package
from smart_scraper_architecture import (
    Event, EventType, DecisionType, ScrapeTargetType,
    IEventProducer, IEventConsumer, IDatabase,
    mock_event_system, mock_database
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

###############################################################################
# Decision Models and Feature Extraction
###############################################################################

class PageFeatures(BaseModel):
    """Features extracted from a web page for decision making."""
    url: str
    title: Optional[str] = None
    meta_description: Optional[str] = None
    content_length: int = 0
    link_count: int = 0
    image_count: int = 0
    has_forms: bool = False
    has_captcha: bool = False
    has_login: bool = False
    product_count: int = 0
    page_depth: int = 0
    keyword_relevance: float = 0.0
    content_type: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True

###############################################################################
# Feature Extractors
###############################################################################

class IFeatureExtractor(ABC):
    """Interface for feature extractors that analyze web pages."""

    @abstractmethod
    async def extract_features(self, url: str, html_content: str, context: Dict[str, Any]) -> PageFeatures:
        """Extract features from a page's HTML content."""
        pass

class BasicFeatureExtractor(IFeatureExtractor):
    """
    Basic implementation of a feature extractor using BeautifulSoup.

    EXTENSION POINT: This can be extended with more sophisticated NLP or
    computer vision techniques for better feature extraction.
    """

    async def extract_features(self, url: str, html_content: str, context: Dict[str, Any]) -> PageFeatures:
        """Extract basic features from HTML using BeautifulSoup."""
        soup = BeautifulSoup(html_content, 'html.parser')

        # Extract basic page information
        title = soup.title.string if soup.title else None

        # Meta description
        meta_desc_tag = soup.find('meta', attrs={'name': 'description'})
        meta_description = meta_desc_tag.get('content') if meta_desc_tag else None

        # Content length
        content_length = len(html_content)

        # Count links
        link_count = len(soup.find_all('a'))

        # Count images
        image_count = len(soup.find_all('img'))

        # Check for forms
        has_forms = len(soup.find_all('form')) > 0

        # Check for potential CAPTCHAs (simple heuristic)
        has_captcha = any(
            captcha_term in html_content.lower()
            for captcha_term in ['captcha', 'recaptcha', 'security check', 'verify you are human']
        )

        # Check for login forms (simple heuristic)
        has_login = any(
            soup.find('input', attrs={'type': input_type})
            for input_type in ['password']
        ) or any(
            login_term in html_content.lower()
            for login_term in ['login', 'sign in', 'signin', 'log in']
        )

        # Count potential product elements based on context['target_type']
        product_count = 0
        target_type = context.get('target_type', '')

        if target_type == ScrapeTargetType.AMAZON:
            product_count = len(soup.find_all('div', attrs={'data-component-type': 's-search-result'}))
        elif target_type == ScrapeTargetType.ETSY:
            product_count = len(soup.find_all('div', class_=lambda c: c and 'listing-card' in c))
        elif target_type == ScrapeTargetType.EBAY:
            product_count = len(soup.find_all('div', class_=lambda c: c and 's-item' in c))
        else:
            # Generic product detection
            product_count = len(soup.find_all(['div', 'li'], class_=lambda c: c and any(
                term in (c or '') for term in ['product', 'item', 'listing']
            )))

        # Page depth (from URL)
        page_depth = url.count('/')

        # Keyword relevance (simple implementation)
        keywords = context.get('keywords', [])
        if keywords:
            text_content = soup.get_text().lower()
            keyword_matches = sum(1 for keyword in keywords if keyword.lower() in text_content)
            keyword_relevance = keyword_matches / len(keywords) if keywords else 0.0
        else:
            keyword_relevance = 0.0

        # Content type estimation
        content_type = None
        if product_count > 0:
            content_type = 'product_listing'
        elif any(term in url for term in ['/product/', '/item/', '/dp/']):
            content_type = 'product_detail'
        elif any(term in url for term in ['/category/', '/c/', '/shop/', '/s-']):
            content_type = 'category'
        elif any(term in url for term in ['/search', 'query', 'q=']):
            content_type = 'search_results'

        return PageFeatures(
            url=url,
            title=title,
            meta_description=meta_description,
            content_length=content_length,
            link_count=link_count,
            image_count=image_count,
            has_forms=has_forms,
            has_captcha=has_captcha,
            has_login=has_login,
            product_count=product_count,
            page_depth=page_depth,
            keyword_relevance=keyword_relevance,
            content_type=content_type
        )

###############################################################################
# Decision Models
###############################################################################

class IDecisionModel(ABC):
    """Interface for decision models that power the AI engine."""

    @abstractmethod
    async def make_decision(self, request: DecisionRequest) -> DecisionResponse:
        """Make a decision based on the request."""
        pass

    @abstractmethod
    async def train(self, training_data: List[Tuple[DecisionRequest, DecisionResponse, Dict[str, Any]]]) -> None:
        """Train the model using historical decisions and outcomes."""
        pass

    @abstractmethod
    async def save_state(self) -> Dict[str, Any]:
        """Save the model state for persistence."""
        pass

    @abstractmethod
    async def load_state(self, state: Dict[str, Any]) -> None:
        """Load the model state from persistence."""
        pass

class RuleBasedDecisionModel(IDecisionModel):
    """
    A rule-based decision model that uses heuristics for decision making.
    This serves as a fallback and baseline for the ML-based models.
    """

    def __init__(self):
        self.rules = {
            DecisionType.NAVIGATION: self._navigation_rules,
            DecisionType.EXTRACTION: self._extraction_rules,
            DecisionType.CHALLENGE_RESPONSE: self._challenge_rules,
            DecisionType.RETRY_STRATEGY: self._retry_rules,
            DecisionType.TERMINATION: self._termination_rules
        }

    async def make_decision(self, request: DecisionRequest) -> DecisionResponse:
        """Apply rules to make a decision."""
        decision_func = self.rules.get(request.decision_type)
        if not decision_func:
            logger.warning(f"No rules defined for decision type: {request.decision_type}")
            return DecisionResponse(
                request_id=str(uuid.uuid4()),
                job_id=request.job_id,
                decision_type=request.decision_type,
                decision={"action": "none"},
                confidence=0.0,
                reasoning="No rules defined for this decision type"
            )

        decision, confidence, reasoning = await decision_func(request)

        return DecisionResponse(
            request_id=str(uuid.uuid4()),
            job_id=request.job_id,
            decision_type=request.decision_type,
            decision=decision,
            confidence=confidence,
            reasoning=reasoning
        )

    async def _navigation_rules(self, request: DecisionRequest) -> Tuple[Dict[str, Any], float, str]:
        """Rules for navigation decisions."""
        features = request.page_features
        if not features:
            return {"action": "stop", "reason": "No page features available"}, 0.5, "Missing features data"

        # If it's a product detail page, don't navigate further
        if features.content_type == 'product_detail':
            return {"action": "extract_only"}, 0.8, "Product detail page detected, prioritizing extraction"

        # If it's a login page, avoid it
        if features.has_login:
            return {"action": "skip"}, 0.7, "Login page detected, skipping to avoid authentication issues"

        # If it has CAPTCHA, be cautious but try to solve simple ones
        if features.has_captcha:
            return {"action": "solve_captcha", "type": "simple"}, 0.6, "CAPTCHA detected, attempting simple solution"

        # For product listings with high relevance, prioritize extraction and then navigate to detail pages
        if features.content_type == 'product_listing' and features.keyword_relevance > 0.7:
            return {
                "action": "extract_and_navigate",
                "priorities": ["product_links", "pagination"]
            }, 0.9, "High-relevance product listing found, extracting products and navigating to detail pages"

        # For category pages, navigate to subcategories or product listings
        if features.content_type == 'category':
            return {
                "action": "navigate",
                "priorities": ["subcategory_links", "product_listing_links"]
            }, 0.8, "Category page detected, navigating to subcategories and product listings"

        # For search results, navigate to product listings
        if features.content_type == 'search_results':
            return {
                "action": "navigate",
                "priorities": ["product_links", "pagination"]
            }, 0.8, "Search results page detected, navigating to products"

        # Default behavior for other pages
        return {
            "action": "navigate",
            "priorities": ["product_links", "category_links", "search_links"]
        }, 0.5, "Generic page detected, following general navigation priorities"

    async def _extraction_rules(self, request: DecisionRequest) -> Tuple[Dict[str, Any], float, str]:
        """Rules for extraction decisions."""
        features = request.page_features
        if not features:
            return {"action": "skip", "reason": "No page features available"}, 0.5, "Missing features data"

        # For product detail pages, extract all product information
        if features.content_type == 'product_detail':
            return {
                "action": "extract",
                "elements": [
                    "product_title", "product_price", "product_description",
                    "product_images", "product_ratings", "product_reviews",
                    "product_specifications", "seller_info"
                ],
                "priority": "high"
            }, 0.9, "Product detail page detected, extracting all product information"

        # For product listings, extract basic product information
        if features.content_type == 'product_listing' or features.product_count > 0:
            return {
                "action": "extract",
                "elements": [
                    "product_titles", "product_prices", "product_images",
                    "product_ratings", "product_links"
                ],
                "priority": "medium"
            }, 0.8, "Product listing page detected, extracting basic product information"

        # For category pages, extract category information
        if features.content_type == 'category':
            return {
                "action": "extract",
                "elements": [
                    "category_name", "subcategories", "breadcrumbs",
                    "category_description", "category_image"
                ],
                "priority": "low"
            }, 0.7, "Category page detected, extracting category information"

        # Default for other pages
        return {
            "action": "extract",
            "elements": ["page_title", "meta_description", "links"],
            "priority": "very_low"
        }, 0.5, "Generic page detected, extracting basic page information"

    async def _challenge_rules(self, request: DecisionRequest) -> Tuple[Dict[str, Any], float, str]:
        """Rules for challenge response decisions."""
        features = request.page_features
        challenge_type = request.context.get("challenge_type", "unknown")

        # For CAPTCHAs, decide based on complexity
        if challenge_type == "captcha" or (features and features.has_captcha):
            captcha_complexity = request.context.get("captcha_complexity", "unknown")

            if captcha_complexity == "simple":
                return {
                    "action": "solve",
                    "method": "ocr",
                    "retry_limit": 3
                }, 0.7, "Simple CAPTCHA detected, attempting OCR solution"
            else:
                return {
                    "action": "avoid",
                    "reason": "Complex CAPTCHA"
                }, 0.8, "Complex CAPTCHA detected, avoiding to prevent detection"

        # For login walls, decide based on context
        if challenge_type == "login" or (features and features.has_login):
            return {
                "action": "avoid",
                "reason": "Login required"
            }, 0.9, "Login wall detected, avoiding authenticated content"

        # For rate limiting
        if challenge_type == "rate_limit":
            return {
                "action": "backoff",
                "delay_seconds": 300,  # 5 minutes
                "retry_limit": 3
            }, 0.9, "Rate limiting detected, implementing backoff strategy"

        # Default for unknown challenges
        return {
            "action": "abort",
            "reason": "Unknown challenge type"
        }, 0.6, "Unknown challenge detected, aborting to prevent detection"

    async def _retry_rules(self, request: DecisionRequest) -> Tuple[Dict[str, Any], float, str]:
        """Rules for retry strategy decisions."""
        error_type = request.context.get("error_type", "unknown")
        retry_count = request.context.get("retry_count", 0)

        # For connection errors
        if error_type in ["connection_error", "timeout", "network_error"]:
            if retry_count < 3:
                return {
                    "action": "retry",
                    "delay_seconds": 5 * (2 ** retry_count),  # Exponential backoff
                    "reason": "Temporary connection issue"
                }, 0.8, f"Connection error, retry {retry_count+1}/3 with exponential backoff"
            else:
                return {
                    "action": "abort",
                    "reason": "Persistent connection issues"
                }, 0.7, "Connection errors persisted after 3 retries, aborting"

        # For server errors (5xx)
        if error_type in ["server_error", "internal_error"]:
            if retry_count < 2:
                return {
                    "action": "retry",
                    "delay_seconds": 10 * (2 ** retry_count),
                    "reason": "Server error may be temporary"
                }, 0.7, f"Server error, retry {retry_count+1}/2 with longer delay"
            else:
                return {
                    "action": "abort",
                    "reason": "Persistent server errors"
                }, 0.8, "Server errors persisted after 2 retries, aborting"

        # For not found errors (404)
        if error_type == "not_found":
            return {
                "action": "abort",
                "reason": "Resource not found"
            }, 0.9, "Resource not found (404), no retry needed"

        # For rate limiting
        if error_type == "rate_limited":
            return {
                "action": "retry",
                "delay_seconds": 300,  # 5 minutes
                "reason": "Rate limited, waiting before retry"
            }, 0.9, "Rate limiting detected, implementing delay before retry"

        # Default for unknown errors
        return {
            "action": "retry" if retry_count < 1 else "abort",
            "delay_seconds": 5 if retry_count < 1 else 0,
            "reason": "Unknown error, trying once more" if retry_count < 1 else "Unknown error persisted"
        }, 0.6, f"Unknown error type, {'retrying once' if retry_count < 1 else 'aborting after retry'}"

    async def _termination_rules(self, request: DecisionRequest) -> Tuple[Dict[str, Any], float, str]:
        """Rules for termination decisions."""
        features = request.page_features
        context = request.context

        # Check if we've reached maximum depth
        current_depth = context.get("current_depth", 0)
        max_depth = context.get("max_depth", 5)

        if current_depth >= max_depth:
            return {
                "action": "terminate",
                "reason": "Maximum depth reached"
            }, 0.9, f"Scraping depth limit reached ({current_depth}/{max_depth})"

        # Check if we've collected enough data
        items_collected = context.get("items_collected", 0)
        target_items = context.get("target_items", 100)

        if items_collected >= target_items:
            return {
                "action": "terminate",
                "reason": "Target data volume reached"
            }, 0.9, f"Target data volume reached ({items_collected}/{target_items} items)"

        # Check if we're seeing diminishing returns
        recent_discoveries = context.get("recent_discoveries", 0)

        if recent_discoveries == 0 and current_depth > 2:
            return {
                "action": "terminate",
                "reason": "Diminishing returns"
            }, 0.8, "No new data discovered in recent scraping, diminishing returns"

        # If on a product detail page and we've extracted the data, terminate this branch
        if features and features.content_type == "product_detail" and context.get("data_extracted", False):
            return {
                "action": "terminate_branch",
                "reason": "Product data extracted completely"
            }, 0.9, "Product detail page fully extracted, terminating this branch"

        # Default - continue scraping
        return {
            "action": "continue",
            "reason": "Scraping targets not yet met"
        }, 0.7, "Continuing scraping, targets not yet met"

    async def train(self, training_data: List[Tuple[DecisionRequest, DecisionResponse, Dict[str, Any]]]) -> None:
        """Rule-based models don't learn, but we log the data for potential future use."""
        logger.info(f"Received {len(training_data)} training examples (rule-based model doesn't train)")

    async def save_state(self) -> Dict[str, Any]:
        """Save model state (no state for rule-based model)."""
        return {}

    async def load_state(self, state: Dict[str, Any]) -> None:
        """Load model state (no state for rule-based model)."""
        pass

# Future ML model implementation placeholder
class MLDecisionModel(IDecisionModel):
    """
    Machine learning based decision model.

    EXTENSION POINT: This can be implemented with a variety of ML techniques including
    reinforcement learning, supervised learning from expert demonstrations, or
    a hybrid approach combining rules and ML.
    """

    def __init__(self):
        self.rule_based_fallback = RuleBasedDecisionModel()
        self.model_ready = False
        self.training_data = []
        self.model_state = {}

    async def make_decision(self, request: DecisionRequest) -> DecisionResponse:
        """Make a decision using ML model or fall back to rules if not ready."""
        if not self.model_ready:
            # Fall back to rule-based model
            response = await self.rule_based_fallback.make_decision(request)
            response.confidence *= 0.8  # Reduce confidence as we're using fallback
            response.reasoning = f"ML model not ready, using rule-based fallback. {response.reasoning}"
            return response

        # Placeholder for ML-based decision logic
        # In a real implementation, this would use the loaded model to make predictions

        # For now, we'll just use the rule-based model
        response = await self.rule_based_fallback.make_decision(request)
        response.reasoning = f"ML model placeholder using rule-based logic. {response.reasoning}"
        return response

    async def train(self, training_data: List[Tuple[DecisionRequest, DecisionResponse, Dict[str, Any]]]) -> None:
        """Train the ML model with the provided data."""
        # Add new data to the training set
        self.training_data.extend(training_data)
        logger.info(f"Added {len(training_data)} examples to training data (total: {len(self.training_data)})")

        # In a real implementation, this would train or update the model
        # For now, we'll just log that we received training data
        if len(self.training_data) >= 100:
            logger.info("Would train model here (placeholder)")
            # self.model_ready = True

    async def save_state(self) -> Dict[str, Any]:
        """Save the ML model state."""
        return {
            "model_ready": self.model_ready,
            "training_data_count": len(self.training_data),
            # "model_weights": ...,  # In a real implementation, this would include model weights
        }

    async def load_state(self, state: Dict[str, Any]) -> None:
        """Load the ML model state."""
        self.model_ready = state.get("model_ready", False)
        # In a real implementation, this would load the model weights and parameters

###############################################################################
# AI Decision Engine Service
###############################################################################

class AIDecisionEngine(IEventProducer, IEventConsumer):
    """
    AI-powered decision engine for the smart scraper system.
    This service handles decision requests from the scraper and provides
    intelligent responses based on page content and historical performance.
    """

    def __init__(self, database: IDatabase, component_name: str = "ai_decision_engine"):
        """
        Initialize the AI Decision Engine.

        Args:
            database: Database interface for storing and retrieving model data
            component_name: Name of this component for event production
        """
        self.database = database
        self.component_name = component_name

        # Decision models
        self.decision_models = {
            "rule_based": RuleBasedDecisionModel(),
            "ml_based": MLDecisionModel()
        }
        self.active_model = "rule_based"  # Default to rule-based initially

        # Feature extractor
        self.feature_extractor = BasicFeatureExtractor()

        # Topics
        self.decision_topic = "scrape_decisions"
        self.data_topic = "scraped_data"
        self.training_topic = "training_data"

        # State
        self.pending_decisions = {}
        self.decision_history = []
        self.training_queue = []

        # Settings
        self.decision_timeout = 5.0  # seconds
        self.training_batch_size = 10
        self.training_interval = 300  # seconds (5 minutes)

    async def initialize(self) -> None:
        """Initialize the engine and connect to required services."""
        logger.info("Initializing AI Decision Engine")
        await self.database.connect()

        # Load model state
        await self._load_model_state()

        # Register event handlers
        await self.register_handlers()

        # Start background tasks
        asyncio.create_task(self._periodic_training())

    async def shutdown(self) -> None:
        """Shut down the engine gracefully."""
        logger.info("Shutting down AI Decision Engine")

        # Save model state
        await self._save_model_state()

        await self.database.disconnect()

    async def _load_model_state(self) -> None:
        """Load model state from the database."""
        try:
            # Try to load state for each model
            for model_name in self.decision_models:
                state = await self.database.retrieve("model_states", model_name)
                if state:
                    await self.decision_models[model_name].load_state(state)
                    logger.info(f"Loaded state for model: {model_name}")

            # Check if ML model is ready and switch to it if so
            ml_model = self.decision_models.get("ml_based")
            if ml_model and hasattr(ml_model, "model_ready") and ml_model.model_ready:
                self.active_model = "ml_based"
                logger.info("Using ML-based decision model")
            else:
                logger.info("Using rule-based decision model")

        except Exception as e:
            logger.error(f"Error loading model state: {str(e)}")

    async def _save_model_state(self) -> None:
        """Save model state to the database."""
        try:
            # Save state for each model
            for model_name, model in self.decision_models.items():
                state = await model.save_state()
                await self.database.store("model_states", {
                    "id": model_name,
                    "state": state,
                    "updated_at": datetime.datetime.now()
                })
                logger.info(f"Saved state for model: {model_name}")
        except Exception as e:
            logger.error(f"Error saving model state: {str(e)}")

    async def register_handlers(self) -> None:
        """Register event handlers."""
        await mock_event_system.subscribe(
            self.decision_topic,
            self.handle_event
        )
        await mock_event_system.subscribe(
            self.data_topic,
            self.handle_event
        )

    async def produce_event(self, event: Event) -> bool:
        """Produce an event to the event system."""
        try:
            topic = self._get_topic_for_event(event.type)
            await mock_event_system.publish(topic, event)
            return True
        except Exception as e:
            logger.error(f"Failed to produce event: {str(e)}")
            return False

    def _get_topic_for_event(self, event_type: EventType) -> str:
        """Map event types to topics."""
        if event_type in [EventType.SCRAPE_DECISION_NEEDED, EventType.SCRAPE_DECISION_MADE]:
            return self.decision_topic
        elif event_type in [EventType.RAW_DATA_COLLECTED, EventType.DATA_TRANSFORMED]:
            return self.data_topic
        elif event_type == EventType.TRAINING_DATA_CAPTURED:
            return self.training_topic
        else:
            return "default"

    async def handle_event(self, event: Event) -> None:
        """Handle incoming events."""
        logger.info(f"Handling event of type {event.type}")

        if event.type == EventType.SCRAPE_DECISION_NEEDED:
            await self._handle_decision_needed(event)
        elif event.type == EventType.RAW_DATA_COLLECTED:
            await self._handle_raw_data(event)

    async def _handle_decision_needed(self, event: Event) -> None:
        """Handle requests for decisions."""
        try:
            # Extract the decision request from the event
            request_data = event.payload.get("request", {})

            # Create a DecisionRequest object
            request = DecisionRequest(**request_data)

            # Extract features if HTML content is provided and no features yet
            if not request.page_features and "html_content" in request.context:
                html_content = request.context["html_content"]
                features = await self.feature_extractor.extract_features(
                    request.url, html_content, request.context
                )
                request.page_features = features

            # Get the active decision model
            model = self.decision_models[self.active_model]

            # Make a decision
            response = await model.make_decision(request)

            # Store in decision history
            self.decision_history.append((request, response))
            if len(self.decision_history) > 1000:
                self.decision_history = self.decision_history[-1000:]

            # Create and send decision made event
            decision_event = Event(
                id=str(uuid.uuid4()),
                type=EventType.SCRAPE_DECISION_MADE,
                producer=self.component_name,
                payload={
                    "job_id": request.job_id,
                    "request_id": response.request_id,
                    "decision_type": response.decision_type,
                    "decision": response.decision,
                    "confidence": response.confidence,
                    "reasoning": response.reasoning
                }
            )

            await self.produce_event(decision_event)

        except Exception as e:
            logger.error(f"Error handling decision request: {str(e)}")

            # Send a fallback decision
            fallback_event = Event(
                id=str(uuid.uuid4()),
                type=EventType.SCRAPE_DECISION_MADE,
                producer=self.component_name,
                payload={
                    "job_id": event.payload.get("job_id", "unknown"),
                    "request_id": event.payload.get("request_id", str(uuid.uuid4())),
                    "decision_type": event.payload.get("decision_type", "unknown"),
                    "decision": {"action": "abort", "reason": "Decision engine error"},
                    "confidence": 0.0,
                    "reasoning": f"Error in decision engine: {str(e)}"
                }
            )

            await self.produce_event(fallback_event)

    async def _handle_raw_data(self, event: Event) -> None:
        """
        Handle raw scraped data events.
        This is used to collect training data by matching decisions with outcomes.
        """
        job_id = event.payload.get("job_id", "")
        url = event.payload.get("url", "")
        data = event.payload.get("data", {})

        # Find any decisions made for this job and URL
        matching_decisions = []
        for request, response in self.decision_history:
            if request.job_id == job_id and request.url == url:
                matching_decisions.append((request, response))

        # If we found matching decisions, add to training queue
        if matching_decisions:
            for request, response in matching_decisions:
                outcome = {
                    "data_collected": bool(data),
                    "data_size": len(str(data)),
                    "timestamp": datetime.datetime.now()
                }

                self.training_queue.append((request, response, outcome))

            logger.info(f"Added {len(matching_decisions)} decisions to training queue")

            # If we have enough data, trigger training
            if len(self.training_queue) >= self.training_batch_size:
                asyncio.create_task(self._train_models())

    async def _periodic_training(self) -> None:
        """Periodically train models with accumulated data."""
        while True:
            try:
                await asyncio.sleep(self.training_interval)

                if self.training_queue:
                    logger.info(f"Periodic training triggered with {len(self.training_queue)} examples")
                    await self._train_models()

                    # Save model state after training
                    await self._save_model_state()
            except Exception as e:
                logger.error(f"Error in periodic training: {str(e)}")

    async def _train_models(self) -> None:
        """Train all models with the current training queue."""
        if not self.training_queue:
            return

        logger.info(f"Training models with {len(self.training_queue)} examples")

        # Train each model
        for model_name, model in self.decision_models.items():
            await model.train(self.training_queue)

        # Clear the queue
        self.training_queue = []

        # Check if ML model is ready and switch to it
        ml_model = self.decision_models.get("ml_based")
        if ml_model and hasattr(ml_model, "model_ready") and ml_model.model_ready:
            if self.active_model != "ml_based":
                logger.info("Switching to ML-based decision model")
                self.active_model = "ml_based"

    async def make_decision(self,
                            job_id: str,
                            url: str,
                            decision_type: DecisionType,
                            html_content: str,
                            context: Dict[str, Any] = None) -> DecisionResponse:
        """
        Make a decision directly (used for testing or direct integration).

        Args:
            job_id: ID of the scraping job
            url: URL being scraped
            decision_type: Type of decision needed
            html_content: HTML content of the page
            context: Additional context for the decision

        Returns:
            DecisionResponse: The decision made by the engine
        """
        if context is None:
            context = {}

        # Create a request
        request = DecisionRequest(
            job_id=job_id,
            url=url,
            decision_type=decision_type,
            context={**context, "html_content": html_content}
        )

        # Extract features
        features = await self.feature_extractor.extract_features(url, html_content, context)
        request.page_features = features

        # Get the active model
        model = self.decision_models[self.active_model]

        # Make decision
        response = await model.make_decision(request)

        # Add to history
        self.decision_history.append((request, response))
        if len(self.decision_history) > 1000:
            self.decision_history = self.decision_history[-1000:]

        return response

# Usage example (in production, this would be in a separate file)
async def demo_decision_engine():
    """Demonstrate the AIDecisionEngine functionality."""
    engine = AIDecisionEngine(mock_database)
    await engine.initialize()

    # Sample HTML content
    sample_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sample Product Page</title>
        <meta name="description" content="This is a sample product page for testing">
    </head>
    <body>
        <h1>Sample Product</h1>
        <div class="product-price">$99.99</div>
        <div class="product-description">
            This is a sample product description.
        </div>
        <div class="product-rating">4.5/5 stars</div>
        <div class="related-products">
            <div class="product-card">Related Product 1</div>
            <div class="product-card">Related Product 2</div>
            <div class="product-card">Related Product 3</div>
        </div>
    </body>
    </html>
    """

    # Make a decision
    decision = await engine.make_decision(
        job_id="test_job_1",
        url="https://example.com/product/123",
        decision_type=DecisionType.NAVIGATION,
        html_content=sample_html,
        context={"target_type": ScrapeTargetType.AMAZON}
    )

    logger.info(f"Decision: {decision.decision}")
    logger.info(f"Confidence: {decision.confidence}")
    logger.info(f"Reasoning: {decision.reasoning}")

    # Shut down
    await engine.shutdown()

if __name__ == "__main__":
    asyncio.run(demo_decision_engine())

class DecisionRequest(BaseModel):
    """Request for a decision from the AI engine."""
    job_id: str
    url: str
    decision_type: DecisionType
    context: Dict[str, Any] = Field(default_factory=dict)
    page_features: Optional[PageFeatures] = None
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.now)

    class Config:
        arbitrary_types_allowed = True

class DecisionResponse(BaseModel):
    """Response containing a decision from the AI engine."""
    request_id: str
    job_id: str
    decision_type: DecisionType
    decision: Dict[str, Any]
    confidence: float = 0.0
    reasoning: Optional[str] = None
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.now)

    class Config:
        arbitrary_types_allowed = True