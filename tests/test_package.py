import handdraw


def test_package_has_a_version():
    assert isinstance(handdraw.__version__, str)
    assert handdraw.__version__ != ""
