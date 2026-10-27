from unittest.mock import MagicMock
from cloud_aws.dynamo import DynamoVectorStore

DOC = 'a' * 24


def test_delete_private_scopes_partition():
    table = MagicMock()
    table.query.return_value = {'Items': [{'pk': 'USER#alice#DOC', 'sk': DOC + '#0001'}]}
    result = DynamoVectorStore(table).delete_private(DOC, owner='alice')
    assert result == 1
    assert table.delete_item.call_args.kwargs['Key'] == {'pk': 'USER#alice#DOC', 'sk': DOC + '#0001'}
    expr = table.query.call_args.kwargs['KeyConditionExpression']
    assert expr is not None


def test_delete_private_not_found():
    table = MagicMock()
    table.query.return_value = {'Items': []}
    assert DynamoVectorStore(table).delete_private(DOC, owner='alice') == 0
    table.delete_item.assert_not_called()


def test_delete_private_fails_closed_if_over_limit():
    import pytest
    table = MagicMock()
    table.query.return_value = {'Items': [{'pk': 'USER#alice#DOC','sk': f'{DOC}#{i:04}'} for i in range(13)]}
    with pytest.raises(ValueError):
        DynamoVectorStore(table).delete_private(DOC, owner='alice')
    table.delete_item.assert_not_called()


def test_delete_private_rejects_missing_owner():
    import pytest
    with pytest.raises(ValueError):
        DynamoVectorStore(MagicMock()).delete_private(DOC, owner='')
