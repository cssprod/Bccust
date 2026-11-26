"""
Text message parser for various export formats (iMessage, WhatsApp, SMS, generic).
Extracts: timestamp, sender, message body.
"""
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Message:
    timestamp: datetime
    sender: str
    body: str
    raw_line: str


# Common timestamp patterns
PATTERNS = [
    # iMessage: "1/15/24, 2:30 PM - John: Hello"
    re.compile(r'^(\d{1,2}/\d{1,2}/\d{2,4}),\s*(\d{1,2}:\d{2}\s*[AP]M)\s*-\s*([^:]+):\s*(.+)$'),
    # WhatsApp: "[1/15/24, 2:30:45 PM] John: Hello"
    re.compile(r'^\[(\d{1,2}/\d{1,2}/\d{2,4}),\s*(\d{1,2}:\d{2}:\d{2}\s*[AP]M)\]\s*([^:]+):\s*(.+)$'),
    # Generic: "2024-01-15 14:30:00 - John: Hello"
    re.compile(r'^(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})\s*-\s*([^:]+):\s*(.+)$'),
    # SMS: "Jan 15, 2024 2:30 PM - John: Hello"
    re.compile(r'^([A-Za-z]{3}\s+\d{1,2},\s+\d{4})\s+(\d{1,2}:\d{2}\s*[AP]M)\s*-\s*([^:]+):\s*(.+)$'),
    # Simple: "John (2:30 PM): Hello"
    re.compile(r'^([^(]+)\s*\((\d{1,2}:\d{2}\s*[AP]M)\):\s*(.+)$'),
]


def parse_timestamp(date_str: str, time_str: str) -> Optional[datetime]:
    """Try multiple timestamp formats."""
    formats = [
        "%m/%d/%y %I:%M %p",
        "%m/%d/%Y %I:%M %p",
        "%m/%d/%y %I:%M:%S %p",
        "%m/%d/%Y %I:%M:%S %p",
        "%Y-%m-%d %H:%M:%S",
        "%b %d, %Y %I:%M %p",
    ]
    combined = f"{date_str} {time_str}"
    for fmt in formats:
        try:
            return datetime.strptime(combined, fmt)
        except ValueError:
            continue
    return None


def parse_messages(text: str, sender_aliases: dict = None) -> list[Message]:
    """
    Parse raw text into Message objects.
    sender_aliases: optional dict to normalize sender names (e.g., {"Mom": "Respondent"})
    """
    messages = []
    lines = text.strip().split('\n')
    current_msg = None
    
    for line in lines:
        line = line.rstrip()
        if not line:
            continue
            
        parsed = False
        for pattern in PATTERNS:
            match = pattern.match(line)
            if match:
                groups = match.groups()
                if len(groups) == 4:
                    date_str, time_str, sender, body = groups
                    timestamp = parse_timestamp(date_str, time_str)
                elif len(groups) == 3:
                    sender, time_str, body = groups
                    # Assume today's date for time-only formats
                    timestamp = parse_timestamp(datetime.now().strftime("%m/%d/%y"), time_str)
                else:
                    continue
                
                if timestamp and sender and body:
                    sender = sender.strip()
                    if sender_aliases and sender in sender_aliases:
                        sender = sender_aliases[sender]
                    current_msg = Message(
                        timestamp=timestamp,
                        sender=sender,
                        body=body.strip(),
                        raw_line=line
                    )
                    messages.append(current_msg)
                    parsed = True
                    break
        
        # Continuation line (multi-line message)
        if not parsed and current_msg:
            current_msg.body += "\n" + line
            current_msg.raw_line += "\n" + line
    
    # Sort by timestamp
    messages.sort(key=lambda m: m.timestamp)
    return messages


def chunk_messages(messages: list[Message], chunk_size: int = 50, overlap: int = 5) -> list[list[Message]]:
    """Split messages into overlapping chunks for LLM processing."""
    if len(messages) <= chunk_size:
        return [messages]
    
    chunks = []
    for i in range(0, len(messages), chunk_size - overlap):
        chunk = messages[i:i + chunk_size]
        chunks.append(chunk)
        if i + chunk_size >= len(messages):
            break
    return chunks


def format_chunk_for_llm(messages: list[Message]) -> str:
    """Format a chunk of messages for LLM analysis."""
    lines = []
    for msg in messages:
        ts = msg.timestamp.strftime("%Y-%m-%d %I:%M %p")
        lines.append(f"[{ts}] {msg.sender}: {msg.body}")
    return "\n".join(lines)
