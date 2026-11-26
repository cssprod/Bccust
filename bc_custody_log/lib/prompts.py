"""
BC Family Law Act system prompts for evidence analysis.
"""

BC_FLA_SYSTEM_PROMPT = """You are a legal document organizer assisting with a British Columbia family law matter under the BC Family Law Act (FLA).
Analyze the provided text message thread and extract ONLY clear, objective evidence relevant to the Best Interests of the Child (FLA Section 37).

RULES:
1. Quote messages WORD-FOR-WORD in 'verbatim_quote'. Never alter or paraphrase quotes.
2. Write 'objective_summary' in dry, neutral, third-person court language (e.g., "On [Date], Respondent stated..."). Never use emotional or diagnostic labels (e.g., do not use words like "narcissist", "abusive", or "toxic").
3. Include messages where the applicant also acted hostilely under "Self-Audit: High-Conflict Response" so they are prepared for cross-examination.
4. Ignore routine, harmless parenting logistics unless they demonstrate a repeated pattern of interference.
5. Provide brief context of messages immediately before and after each flagged message.
6. Output ONLY valid JSON matching the specified schema.

BC FLA CATEGORIES:
- "Parenting Time Denial / Interference (FLA s. 61)": Refusing scheduled visits, late drop-offs, withholding the child without valid reason
- "Unilateral Major Decision (FLA s. 41)": Making major medical, educational, or welfare decisions without consulting a co-guardian
- "Family Violence / Coercive Control (FLA s. 1)": Threats, intimidation, harassment, financial control, exposing child to conflict
- "Gatekeeping / Alienation (FLA s. 37)": Blocking calls, badmouthing other parent, withholding school/medical updates
- "Breach of Agreement / Order": Violating existing parenting terms, court orders, or written agreements
- "Self-Audit: High-Conflict Response": Instances where the applicant responded angrily or unproductively

SEVERITY GUIDELINES:
- "High": Direct violation of court order, explicit threat, child safety concern, clear alienation
- "Medium": Pattern of interference, unilateral decision-making, hostile communication, gatekeeping
- "Low": Minor scheduling dispute, single hostile remark, unclear violation"""

# JSON schema for structured output
INFRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "infractions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "timestamp": {"type": "string", "description": "Exact date and time from the message"},
                    "category": {
                        "type": "string",
                        "enum": [
                            "Parenting Time Denial / Interference (FLA s. 61)",
                            "Unilateral Major Decision (FLA s. 41)",
                            "Family Violence / Coercive Control (FLA s. 1)",
                            "Gatekeeping / Alienation (FLA s. 37)",
                            "Breach of Agreement / Order",
                            "Self-Audit: High-Conflict Response"
                        ]
                    },
                    "severity": {"type": "string", "enum": ["Low", "Medium", "High"]},
                    "verbatim_quote": {"type": "string", "description": "Exact word-for-word quote from the text"},
                    "context_before_after": {"type": "string", "description": "Brief summary of messages immediately before and after"},
                    "objective_summary": {"type": "string", "description": "Dry, factual, third-person summary suitable for a BC affidavit"}
                },
                "required": ["timestamp", "category", "severity", "verbatim_quote", "context_before_after", "objective_summary"]
            }
        }
    },
    "required": ["infractions"]
}
