"""Input Sanitization for LLM Prompts

Prevents prompt injection attacks by sanitizing user inputs before
incorporating into LLM prompts.

Based on L208 lines 541-548 (Security Protocols - Prompt Injection Prevention)
"""

from typing import Optional
import re
import html


class InputSanitizer:
    """Sanitizes user inputs to prevent prompt injection

    Design Decision: Defense-in-depth approach:
    1. Remove special tokens that could manipulate LLM
    2. Escape HTML to prevent rendering attacks
    3. Use delimiters to separate instructions from user content
    4. Validate length constraints

    Based on L208 lines 541-548 (Prompt Injection Prevention)
    """

    def __init__(self, max_length: int = 50000):
        """Initialize input sanitizer

        Args:
            max_length: Maximum allowed input length
        """
        self.max_length = max_length

    def sanitize(self, user_input: str) -> str:
        """Sanitize user input for safe use in LLM prompts

        Args:
            user_input: Raw user input

        Returns:
            Sanitized input safe for LLM prompts

        Raises:
            ValueError: If input exceeds max_length
        """
        if len(user_input) > self.max_length:
            raise ValueError(
                f"Input length {len(user_input)} exceeds maximum {self.max_length}"
            )

        # Remove special tokens that could confuse LLM
        sanitized = self._remove_special_tokens(user_input)

        # Escape HTML
        sanitized = html.escape(sanitized)

        # Remove excessive whitespace
        sanitized = self._normalize_whitespace(sanitized)

        return sanitized

    def wrap_with_delimiters(
        self,
        user_content: str,
        delimiter: str = "USER_CONTENT"
    ) -> str:
        """Wrap user content with XML-style delimiters

        This clearly separates instructions from user-provided content,
        making it harder for users to inject instructions.

        Example:
            <USER_CONTENT>
            User's potentially malicious text here
            </USER_CONTENT>

        Based on L208 line 545 (Use delimiter tokens)

        Args:
            user_content: User content to wrap
            delimiter: Delimiter name (default: USER_CONTENT)

        Returns:
            Wrapped content
        """
        return f"<{delimiter}>\n{user_content}\n</{delimiter}>"

    def build_safe_prompt(
        self,
        system_instruction: str,
        user_content: str
    ) -> str:
        """Build a safe prompt with clear separation

        Args:
            system_instruction: System-level instruction for LLM
            user_content: User-provided content

        Returns:
            Complete prompt with sanitized content
        """
        sanitized_content = self.sanitize(user_content)
        wrapped_content = self.wrap_with_delimiters(sanitized_content)

        return f"{system_instruction}\n\n{wrapped_content}"

    def _remove_special_tokens(self, text: str) -> str:
        """Remove special tokens that could manipulate LLM behavior

        Args:
            text: Text to clean

        Returns:
            Text with special tokens removed
        """
        # Remove common LLM control tokens
        # Pattern: <|token_name|>
        text = re.sub(r'<\|.*?\|>', '', text)

        # Remove potential role injection attempts
        # Pattern: [SYSTEM], [ASSISTANT], [USER], etc.
        text = re.sub(r'\[(SYSTEM|ASSISTANT|USER|INSTRUCTION)\]', '', text, flags=re.IGNORECASE)

        # Remove markdown code fence injection attempts
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)

        return text

    def _normalize_whitespace(self, text: str) -> str:
        """Normalize excessive whitespace

        Args:
            text: Text to normalize

        Returns:
            Text with normalized whitespace
        """
        # Replace multiple spaces with single space
        text = re.sub(r' +', ' ', text)

        # Replace multiple newlines with maximum of 2
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Trim leading/trailing whitespace
        text = text.strip()

        return text

    @staticmethod
    def validate_output(llm_output: str) -> bool:
        """Validate that LLM output doesn't contain manipulation attempts

        Checks if the model attempted to inject instructions back.

        Based on L208 line 547 (Validate model outputs)

        Args:
            llm_output: Output from LLM

        Returns:
            True if output appears safe, False if suspicious
        """
        # Check for control token injection attempts
        if re.search(r'<\|.*?\|>', llm_output):
            return False

        # Check for role injection in output
        if re.search(r'\[(SYSTEM|ASSISTANT|USER)\]:', llm_output, re.IGNORECASE):
            return False

        # Check for prompt template injection
        if re.search(r'You are a helpful assistant', llm_output, re.IGNORECASE):
            return False

        return True


class PromptBuilder:
    """Helper class for building safe prompts

    Provides templates and utilities for constructing prompts
    that are resistant to injection attacks.
    """

    def __init__(self, sanitizer: Optional[InputSanitizer] = None):
        """Initialize prompt builder

        Args:
            sanitizer: Input sanitizer (creates default if None)
        """
        self.sanitizer = sanitizer or InputSanitizer()

    def build_extraction_prompt(
        self,
        document: str,  # Renamed from document_text for API consistency
        extraction_schema: dict  # Changed from str to dict per API spec
    ) -> str:
        """Build prompt for data extraction

        Args:
            document: Document to extract from
            extraction_schema: Schema dict describing what to extract

        Returns:
            Safe prompt for extraction
        """
        # Convert schema dict to string for prompt
        import json
        schema_str = json.dumps(extraction_schema, indent=2)

        instruction = f"""Extract information according to this schema:
{schema_str}

Respond ONLY with the extracted data in the specified format.
Do not include explanations or additional commentary."""

        return self.sanitizer.build_safe_prompt(instruction, document)

    def build_summarization_prompt(
        self,
        document: str,  # Renamed from document_text for API consistency
        max_length: int = None  # Renamed from max_summary_length, made optional per API spec
    ) -> str:
        """Build prompt for document summarization

        Args:
            document: Document to summarize
            max_length: Maximum summary length in words (optional)

        Returns:
            Safe prompt for summarization
        """
        if max_length:
            instruction = f"""Summarize the following document in {max_length} words or less.
Focus on the key points and main ideas.
Do not include opinions or interpretations not present in the original text."""
        else:
            instruction = """Summarize the following document.
Focus on the key points and main ideas.
Do not include opinions or interpretations not present in the original text."""

        return self.sanitizer.build_safe_prompt(instruction, document)

    def build_classification_prompt(
        self,
        document: str,  # Renamed from document_text for API consistency
        categories: list  # List[str] per API spec
    ) -> str:
        """Build prompt for document classification

        Args:
            document: Document to classify
            categories: List of possible categories

        Returns:
            Safe prompt for classification
        """
        categories_str = ", ".join(categories)

        instruction = f"""Classify the following document into ONE of these categories:
{categories_str}

Respond with ONLY the category name, nothing else."""

        return self.sanitizer.build_safe_prompt(instruction, document)
