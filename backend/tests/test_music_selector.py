
import unittest
from unittest.mock import patch, MagicMock
import os

# Add the parent directory to the path to allow module imports
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.music_selector import select_music, MUSIC_LIBRARY

class TestMusicSelector(unittest.TestCase):

    @patch('modules.music_selector.os.path.exists', return_value=True)
    @patch('modules.music_selector.random.choice')
    def test_happy_script_selects_happy_music(self, mock_random_choice, mock_exists):
        """Test that a positive script selects music from the 'happy' category."""
        happy_script = "This is a wonderful, joyous, and amazing day!"
        
        # Make random.choice return a predictable value
        expected_song = MUSIC_LIBRARY['happy'][0]
        mock_random_choice.return_value = expected_song
        
        result = select_music(happy_script)
        
        # Check that random.choice was called with the list of happy songs
        self.assertEqual(len(mock_random_choice.call_args[0][0]), len(MUSIC_LIBRARY['happy']))
        self.assertIn(expected_song, mock_random_choice.call_args[0][0])
        
        # Check that the result is the one we forced
        self.assertEqual(result, expected_song)

    @patch('modules.music_selector.os.path.exists', return_value=True)
    @patch('modules.music_selector.random.choice')
    def test_sad_script_selects_sad_music(self, mock_random_choice, mock_exists):
        """Test that a negative script selects music from the 'sad' category."""
        sad_script = "This is a terrible, awful, and sad story."
        
        expected_song = MUSIC_LIBRARY['sad'][0]
        mock_random_choice.return_value = expected_song
        
        result = select_music(sad_script)
        
        self.assertEqual(len(mock_random_choice.call_args[0][0]), len(MUSIC_LIBRARY['sad']))
        self.assertIn(expected_song, mock_random_choice.call_args[0][0])
        self.assertEqual(result, expected_song)

    @patch('modules.music_selector.os.path.exists', return_value=True)
    @patch('modules.music_selector.random.choice')
    def test_neutral_script_selects_inspiring_music(self, mock_random_choice, mock_exists):
        """Test that a neutral script selects music from the 'inspiring' category."""
        neutral_script = "This is a script about a table and a chair."
        
        expected_song = MUSIC_LIBRARY['inspiring'][0]
        mock_random_choice.return_value = expected_song
        
        result = select_music(neutral_script)
        
        self.assertEqual(len(mock_random_choice.call_args[0][0]), len(MUSIC_LIBRARY['inspiring']))
        self.assertIn(expected_song, mock_random_choice.call_args[0][0])
        self.assertEqual(result, expected_song)

    @patch('modules.music_selector.os.path.exists', return_value=False)
    def test_no_existing_files_returns_none(self, mock_exists):
        """Test that if no music files exist for a mood, None is returned."""
        any_script = "This can be any script."
        result = select_music(any_script)
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
