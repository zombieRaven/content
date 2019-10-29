import pytest

import demistomock as demisto


def test_test_module(mocker):
    mocker.patch.object(demisto, 'params', return_value={

    })
    from SharePoint import test_module
    test_module()