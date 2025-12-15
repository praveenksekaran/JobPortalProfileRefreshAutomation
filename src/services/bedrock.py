"""
Amazon Bedrock integration for AI-powered content mutation
Uses Claude models to make minimal, natural changes to profile text
"""

import json
from typing import Optional

import boto3
from botocore.exceptions import ClientError

from config import AWS_CONFIG, BEDROCK_CONFIG
from src.utils.logger import Logger

logger = Logger('Bedrock')


class BedrockService:
    """Amazon Bedrock client wrapper"""

    def __init__(self):
        self.client = boto3.client('bedrock-runtime', region_name=AWS_CONFIG['region'])

    def mutate_content(self, original_content: str, context: str = '') -> str:
        """
        Mutate content using AI to introduce minimal changes

        Args:
            original_content: Original profile text
            context: Context about what this content represents

        Returns:
            Modified content
        """
        try:
            logger.info('Requesting content mutation from Bedrock', {
                'content_length': len(original_content),
                'context': context,
            })

            prompt = self._build_prompt(original_content, context)
            modified_content = self._invoke_model(prompt)

            logger.info('Successfully mutated content', {
                'original_length': len(original_content),
                'modified_length': len(modified_content),
            })

            return modified_content

        except Exception as error:
            logger.error('Failed to mutate content with Bedrock', error)
            # Fallback: return original content with minor punctuation change
            return self._fallback_mutation(original_content)

    def _build_prompt(self, content: str, context: str) -> str:
        """Build the prompt for content mutation"""
        context_prefix = f'Context: This is a {context} section of a professional profile.\n\n' if context else ''

        return f"""{context_prefix}Original text:
{content}

Task: Make MINIMAL changes to refresh this text while preserving its exact meaning and professional tone. Changes should be subtle and natural, such as:
- Rearranging sentence structure slightly
- Replacing a few words with synonyms
- Adjusting punctuation or formatting
- DO NOT add new information or change the core message
- DO NOT make it longer or shorter by more than 10%
- Keep the same professional level and tone

Provide ONLY the modified text, no explanations or preamble."""

    def _invoke_model(self, prompt: str) -> str:
        """Invoke Bedrock model"""
        payload = {
            'anthropic_version': 'bedrock-2023-05-31',
            'max_tokens': BEDROCK_CONFIG['max_tokens'],
            'temperature': BEDROCK_CONFIG['temperature'],
            'system': BEDROCK_CONFIG['system_prompt'],
            'messages': [
                {
                    'role': 'user',
                    'content': prompt,
                },
            ],
        }

        try:
            response = self.client.invoke_model(
                modelId=BEDROCK_CONFIG['model_id'],
                contentType='application/json',
                accept='application/json',
                body=json.dumps(payload),
            )

            response_body = json.loads(response['body'].read())

            if not response_body.get('content') or not response_body['content'][0].get('text'):
                raise ValueError('Invalid response from Bedrock model')

            return response_body['content'][0]['text'].strip()

        except ClientError as error:
            logger.error('Bedrock API error', error)
            raise

    def _fallback_mutation(self, content: str) -> str:
        """
        Fallback mutation when Bedrock fails
        Makes a simple, safe change to the content
        """
        logger.warn('Using fallback mutation method')

        # Simple fallback: add or remove a period at the end
        if content.endswith('.'):
            return content[:-1] + '.'
        elif content.endswith('!'):
            return content[:-1] + '.'
        else:
            return content + '.'

    def validate_mutation(self, original: str, mutated: str) -> bool:
        """
        Validate that mutated content is acceptable

        Args:
            original: Original content
            mutated: Mutated content

        Returns:
            True if mutation is valid
        """
        # Check that content isn't too different in length
        length_diff = abs(len(mutated) - len(original))
        length_change_percent = (length_diff / len(original)) * 100

        if length_change_percent > 15:
            logger.warn('Mutation changed length by more than 15%', {
                'original': len(original),
                'mutated': len(mutated),
                'change_percent': round(length_change_percent, 2),
            })
            return False

        # Check that content isn't identical
        if original == mutated:
            logger.warn('Mutation produced identical content')
            return False

        return True
