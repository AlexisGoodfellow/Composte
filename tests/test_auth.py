"""Test the auth helpers."""
from composte.auth.auth import hash as h
from composte.auth.auth import verify as v


def test_auth__hash_is_correct(mocker):
    expected_hash = "$pbkdf2-sha256$29000$kPJ.LwUAIGQsZYyRci4FYA$7HIib0d2Df0mRVtxXkAcmOwhJEd.iirqlbVl.cV3uxQ"
    hash_mock = mocker.patch(
        "composte.auth.auth.pbkdf2_sha256.hash", return_value=expected_hash
    )
    assert h("some_value") == expected_hash
    hash_mock.assert_called_once()


def test_auth__hash_can_verify(mocker):
    known_hash = "$pbkdf2-sha256$29000$kPJ.LwUAIGQsZYyRci4FYA$7HIib0d2Df0mRVtxXkAcmOwhJEd.iirqlbVl.cV3uxQ"
    assert v("m", known_hash)
