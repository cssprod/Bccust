"""
Local AI analyzer using Ollama for structured infraction extraction.
"""
import json
import logging
from typing import List, Dict, Optional

import ollama

from lib.prompts import BC_FLA_SYSTEM_PROMPT, INFRACTION_SCHEMA

logger = logging.getLogger(__name__)


class InfractionAnalyzer:
    def __init__(self, model: str = "llama3.1", host: str = "http://localhost:11434"):
        self.model = model
        self.client = ollama.Client(host=host)

    def analyze_chunk(self, chunk_text: str) -> List[Dict]:
        """Analyze a single chunk of messages and return infractions."""
        prompt = (
            f"{BC_FLA_SYSTEM_PROMPT}\n\n"
            f"Output Schema: {json.dumps(INFRACTION_SCHEMA, indent=2)}\n\n"
            f"Conversation:\n{chunk_text}\n\n"
            f"Return valid JSON only."
        )

        try:
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                format="json",
                options={"temperature": 0.1},
            )
            raw = response.get("response", "{}")
            data = json.loads(raw)
            return data.get("infractions", [])
        except Exception as exc:
            logger.error(f"LLM analysis failed: {exc}")
            return []

    def verify_quotes(self, infractions: List[Dict], original_text: str) -> List[Dict]:
        """Filter out infractions whose verbatim quote does not exist in original text."""
        verified = []
        for inf in infractions:
            quote = inf.get("verbatim_quote", "").strip()
            if quote and quote in original_text:
                verified.append(inf)
        return verified

    def analyze_all(self, chunks: List[str], original_text: str) -> List[Dict]:
        """Analyze all chunks, merge results, and verify quotes."""
        all_infractions = []
        for i, chunk in enumerate(chunks):
            logger.info(f"Analyzing chunk {i + 1}/{len(chunks)}")
            infractions = self.analyze_chunk(chunk)
            all_infractions.extend(infractions)

        verified = self.verify_quotes(all_infractions, original_text)
        logger.info(f"Found {len(all_infractions)} infractions, {len(verified)} verified")
        return verified
