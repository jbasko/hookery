import pytest

from hookery import GlobalHook


def test_cannot_register_classmethod_or_staticmethod_as_handler():
    before = GlobalHook('before')

    with pytest.raises(TypeError):
        before(classmethod(lambda cls: None))

    with pytest.raises(TypeError):
        before(staticmethod(lambda: None))
