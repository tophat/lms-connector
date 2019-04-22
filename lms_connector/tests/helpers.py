from mock import Mock


def spy_on(method):
    """
    Spy on a function (record its calls, but don't interrupt their usage).
    Keep these records in a Mock object and store the Mock object as
    an attribute on the function.
    """
    m = Mock()

    def wrapper(*args, **kwargs):
        m(*args, **kwargs)
        return method(*args, **kwargs)

    wrapper.mock = m
    return wrapper
