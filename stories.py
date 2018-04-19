"""
stories
-------

This module implements Business Transaction DSL.

:copyright: (c) 2018 by Artem Malyshev.
:license: BSD, see LICENSE for more details.
"""


__all__ = ["story", "argument", "Result", "Success", "Failure", "Skip"]


import sys


def story(f):

    def wrapper(self, *args, **kwargs):
        return tell_the_story(self, f, args, kwargs)

    wrapper.is_story = True
    wrapper.f = f
    return wrapper


def argument(name):

    def decorator(f):
        if not hasattr(f, "arguments"):
            f.arguments = []
        f.arguments.insert(0, name)
        return f

    return decorator


class Result(object):

    def __init__(self, value=None):
        self.value = value

    def __repr__(self):
        return self.__class__.__name__ + "(" + repr(self.value) + ")"


class Success(object):

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def __repr__(self):
        return self.__class__.__name__ + namespace_representation(self.kwargs)


class Failure(object):

    def __repr__(self):
        return self.__class__.__name__ + "()"


class Skip(object):

    def __repr__(self):
        return self.__class__.__name__ + "()"


undefined = object()


def tell_the_story(obj, f, args, kwargs):

    ctx = Context(validate_arguments(f, args, kwargs))
    the_story = []
    f(Collector(obj, the_story, f))
    skipped = undefined

    for self, method, of in the_story:

        if skipped is not undefined:
            if method is end_of_story and skipped is of:
                skipped = undefined
            continue

        result = method(make_proxy(self, ctx))
        if result is undefined:
            continue

        restype = type(result)
        assert restype in (Result, Success, Failure, Skip)

        if restype is Failure:
            return result

        if restype is Result:
            return result.value

        if restype is Skip:
            skipped = of
            continue

        assert not set(ctx.ns) & set(result.kwargs)
        ctx.ns.update(result.kwargs)


def validate_arguments(f, args, kwargs):

    assert not (args and kwargs)
    arguments = getattr(f, "arguments", [])

    if args:
        assert len(arguments) == len(args)
        return {k: v for k, v in zip(arguments, args)}

    assert set(arguments) == set(kwargs)
    return kwargs


class Context(object):

    def __init__(self, ns):
        self.ns = ns

    def __getattr__(self, name):
        return self.ns[name]

    def __repr__(self):
        return self.__class__.__name__ + namespace_representation(self.ns)


class Collector(object):

    def __init__(self, obj, method_calls, of):
        self.obj = obj
        self.method_calls = method_calls
        self.of = of

    def __getattr__(self, name):

        attribute = getattr(self.obj.__class__, name, undefined)

        if attribute is not undefined:
            if is_story(attribute):
                collect_substory(attribute, self.obj, self.method_calls)
                return lambda: None

            self.method_calls.append((self.obj, attribute, self.of))
            return lambda: None

        attribute = getattr(self.obj, name)
        assert is_story(attribute)
        collect_substory(attribute.__func__, attribute.__self__, self.method_calls)
        return lambda: None


PY3 = sys.version_info[0] >= 3


if PY3:

    def make_proxy(obj, ctx):
        return Proxy(obj, ctx)


else:

    def make_proxy(obj, ctx):

        class ObjectProxy(Proxy, obj.__class__):
            pass

        return ObjectProxy(obj, ctx)


class Proxy(object):

    def __init__(self, obj, ctx):
        self.obj = obj
        self.ctx = ctx

    def __getattr__(self, name):
        return getattr(self.obj, name)


def is_story(attribute):
    return callable(attribute) and getattr(attribute, "is_story", False)


def collect_substory(story, obj, method_calls):

    arguments = getattr(story.f, "arguments", [])

    def validate_substory_arguments(self):
        assert set(arguments) <= set(self.ctx.ns)
        return undefined

    method_calls.append((obj, validate_substory_arguments, story.f))
    story.f(Collector(obj, method_calls, story.f))
    method_calls.append((obj, end_of_story, story.f))


def end_of_story(self):
    return undefined


def namespace_representation(ns):
    return "(" + ", ".join([k + "=" + repr(v) for k, v in ns.items()]) + ")"
