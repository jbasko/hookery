import pytest

from hookery import Hook


def test_cannot_register_classmethod_or_staticmethod_as_handler():
    before = Hook('before')

    with pytest.raises(TypeError):
        before(classmethod(lambda cls: None))

    with pytest.raises(TypeError):
        before(staticmethod(lambda: None))
