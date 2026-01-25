import unittest
from unittest.mock import patch, MagicMock

import datetime
import pandas as pd
import json

class TestFetchData(unittest.TestCase):

    @patch('app.emit')
    @patch('app.yf.download')
    @patch('app.pd.read_csv')
    @patch('app.os.path.exists')
    @patch('app.os.makedirs')
    @patch('app.Helper')
    def test_fetch_data(self, MockHelper, mock_makedirs, mock_exists, mock_read_csv, mock_download, mock_emit):
        pass

if __name__ == '__main__':
    unittest.main()