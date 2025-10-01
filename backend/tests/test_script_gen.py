
import unittest
from unittest.mock import patch, MagicMock
import os

# Add the parent directory to the path to allow module imports
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.script_gen import generate_script

class TestScriptGenerator(unittest.TestCase):

    @patch.dict(os.environ, {}, clear=True)
    def test_raises_error_if_api_key_is_missing(self):
        """Test that generate_script raises RuntimeError if OPENAI_API_KEY is not set."""
        with self.assertRaisesRegex(RuntimeError, "OPENAI_API_KEY is not set"):
            generate_script("A simple prompt", {})

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch('modules.script_gen.OpenAI')
    def test_successful_script_generation(self, MockOpenAI):
        """Test that a successful API call returns the generated script."""
        # Mock the entire client and its response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices[0].message.content = " This is a test script. "
        mock_client.chat.completions.create.return_value = mock_response
        MockOpenAI.return_value = mock_client

        prompt = "A motivational video."
        timestamps = {0: [(0.5, 2.1)], 1: [(3.0, 4.5)]}
        
        result = generate_script(prompt, timestamps)

        # Check that the result is the stripped content from the mock response
        self.assertEqual(result, "This is a test script.")

        # Check that the API was called
        mock_client.chat.completions.create.assert_called_once()
        
        # Check the content of the user message sent to the API
        call_args, _ = mock_client.chat.completions.create.call_args
        user_message = next(m for m in call_args['messages'] if m['role'] == 'user')
        self.assertIn("Prompt: A motivational video.", user_message['content'])
        self.assertIn("Person 0: 0.5s–2.1s", user_message['content'])
        self.assertIn("Person 1: 3.0s–4.5s", user_message['content'])

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch('modules.script_gen.OpenAI')
    def test_empty_response_from_api(self, MockOpenAI):
        """Test that a RuntimeError is raised if the API returns an empty script."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices[0].message.content = ""
        mock_client.chat.completions.create.return_value = mock_response
        MockOpenAI.return_value = mock_client

        with self.assertRaisesRegex(RuntimeError, "Empty script generated"):
            generate_script("A prompt", {})

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch('modules.script_gen.OpenAI')
    def test_api_call_raises_exception(self, MockOpenAI):
        """Test that a RuntimeError is raised if the OpenAI client call fails."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API connection failed")
        MockOpenAI.return_value = mock_client

        with self.assertRaisesRegex(RuntimeError, "OpenAI error: API connection failed"):
            generate_script("A prompt", {})

if __name__ == '__main__':
    unittest.main()
