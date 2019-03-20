import pytest

import examples
from helpers import make_collector
from stories._context import make_context
from stories._history import History
from stories.exceptions import (
    ContextContractError,
    FailureError,
    FailureProtocolError,
    MutationError,
)


def test_context_dir():
    """Show context variables in the `dir` output."""

    class Ctx(object):
        a = 2
        b = 2

    assert dir(make_context(["a", "b"], {"a": 2, "b": 2}, History())) == dir(Ctx())


def test_deny_context_attribute_assignment(c):
    """
    We can't use attribute assignment with `Context` object.
    """

    class T(c.Child, c.AssignMethod):
        pass

    class Q(c.Parent, c.NormalParentMethod, T):
        pass

    class J(c.Parent, c.NormalParentMethod):
        def __init__(self):
            self.x = T().x

    expected = """
Context object is immutable.

Use Success() keyword arguments to expand its scope.
    """.strip()

    # Simple.

    with pytest.raises(MutationError) as exc_info:
        T().x()
    assert str(exc_info.value) == expected

    with pytest.raises(MutationError) as exc_info:
        T().x.run()
    assert str(exc_info.value) == expected

    # Substory inheritance.

    with pytest.raises(MutationError) as exc_info:
        Q().a()
    assert str(exc_info.value) == expected

    with pytest.raises(MutationError) as exc_info:
        Q().a.run()
    assert str(exc_info.value) == expected

    # Substory DI.

    with pytest.raises(MutationError) as exc_info:
        J().a()
    assert str(exc_info.value) == expected

    with pytest.raises(MutationError) as exc_info:
        J().a.run()
    assert str(exc_info.value) == expected


def test_deny_context_attribute_deletion(c):
    """
    We can't use attribute deletion with `Context` object.
    """

    class T(c.Child, c.DeleteMethod):
        pass

    class Q(c.Parent, c.NormalParentMethod, T):
        pass

    class J(c.Parent, c.NormalParentMethod):
        def __init__(self):
            self.x = T().x

    expected = """
Context object is immutable.

Variables can not be removed from Context.
    """.strip()

    # Simple.

    with pytest.raises(MutationError) as exc_info:
        T().x()
    assert str(exc_info.value) == expected

    with pytest.raises(MutationError) as exc_info:
        T().x.run()
    assert str(exc_info.value) == expected

    # Substory inheritance.

    with pytest.raises(MutationError) as exc_info:
        Q().a()
    assert str(exc_info.value) == expected

    with pytest.raises(MutationError) as exc_info:
        Q().a.run()
    assert str(exc_info.value) == expected

    # Substory DI.

    with pytest.raises(MutationError) as exc_info:
        J().a()
    assert str(exc_info.value) == expected

    with pytest.raises(MutationError) as exc_info:
        J().a.run()
    assert str(exc_info.value) == expected


def test_context_representation_with_empty():

    expected = """
Empty.x

Context()
    """.strip()

    getter = make_collector()
    examples.methods.Empty().x()
    assert repr(getter()) == expected

    getter = make_collector()
    examples.methods.Empty().x.run()
    assert repr(getter()) == expected

    expected = """
EmptySubstory.y
  x

Context()
    """.strip()

    getter = make_collector()
    examples.methods.EmptySubstory().y()
    assert repr(getter()) == expected

    getter = make_collector()
    examples.methods.EmptySubstory().y.run()
    assert repr(getter()) == expected

    expected = """
SubstoryDI.y
  start
  before
  x (Empty.x)
  after (returned: 6)

Context:
  spam: 3  # Story argument
  foo: 2   # Set by SubstoryDI.start
  bar: 4   # Set by SubstoryDI.before
    """.strip()

    getter = make_collector()
    examples.methods.SubstoryDI(examples.methods.Empty().x).y(spam=3)
    assert repr(getter()) == expected

    getter = make_collector()
    examples.methods.SubstoryDI(examples.methods.Empty().x).y.run(spam=3)
    assert repr(getter()) == expected


def test_context_representation_with_failure():

    expected = """
Simple.x
  one
  two (failed)

Context:
  foo: 3  # Story argument
  bar: 2  # Story argument
    """.strip()

    getter = make_collector()
    with pytest.raises(FailureError):
        examples.methods.Simple().x(foo=3, bar=2)
    assert repr(getter()) == expected

    getter = make_collector()
    examples.methods.Simple().x.run(foo=3, bar=2)
    assert repr(getter()) == expected

    expected = """
SimpleSubstory.y
  start
  before
  x
    one
    two (failed)

Context:
  spam: 3  # Story argument
  foo: 2   # Set by SimpleSubstory.start
  bar: 4   # Set by SimpleSubstory.before
    """.strip()

    getter = make_collector()
    with pytest.raises(FailureError):
        examples.methods.SimpleSubstory().y(spam=3)
    assert repr(getter()) == expected

    getter = make_collector()
    examples.methods.SimpleSubstory().y.run(spam=3)
    assert repr(getter()) == expected

    expected = """
SubstoryDI.y
  start
  before
  x (Simple.x)
    one
    two (failed)

Context:
  spam: 3  # Story argument
  foo: 2   # Set by SubstoryDI.start
  bar: 4   # Set by SubstoryDI.before
    """.strip()

    getter = make_collector()
    with pytest.raises(FailureError):
        examples.methods.SubstoryDI(examples.methods.Simple().x).y(spam=3)
    assert repr(getter()) == expected

    getter = make_collector()
    examples.methods.SubstoryDI(examples.methods.Simple().x).y.run(spam=3)
    assert repr(getter()) == expected


def test_context_representation_with_failure_reason_list(f):
    class T(f.ChildWithList, f.StringMethod):
        pass

    class Q(f.ParentWithList, f.NormalParentMethod, T):
        pass

    class J(f.ParentWithList, f.NormalParentMethod):
        def __init__(self):
            self.x = T().x

    # Simple.

    expected = """
T.x
  one (failed: 'foo')

Context()
    """.strip()

    getter = make_collector()
    with pytest.raises(FailureError):
        T().x()
    assert repr(getter()) == expected

    getter = make_collector()
    T().x.run()
    assert repr(getter()) == expected

    # Substory inheritance.

    expected = """
Q.a
  before
  x
    one (failed: 'foo')

Context()
    """.strip()

    getter = make_collector()
    with pytest.raises(FailureError):
        Q().a()
    assert repr(getter()) == expected

    getter = make_collector()
    Q().a.run()
    assert repr(getter()) == expected

    # Substory DI.

    expected = """
J.a
  before
  x (T.x)
    one (failed: 'foo')

Context()
    """.strip()

    getter = make_collector()
    with pytest.raises(FailureError):
        J().a()
    assert repr(getter()) == expected

    getter = make_collector()
    J().a.run()
    assert repr(getter()) == expected


def test_context_representation_with_failure_reason_enum(f):
    class T(f.ChildWithEnum, f.EnumMethod):
        pass

    class Q(f.ParentWithEnum, f.NormalParentMethod, T):
        pass

    class J(f.ParentWithEnum, f.NormalParentMethod):
        def __init__(self):
            self.x = T().x

    # Simple.

    expected = """
T.x
  one (failed: <Errors.foo: 1>)

Context()
    """.strip()

    getter = make_collector()
    with pytest.raises(FailureError):
        T().x()
    assert repr(getter()) == expected

    getter = make_collector()
    T().x.run()
    assert repr(getter()) == expected

    # Substory inheritance.

    expected = """
Q.a
  before
  x
    one (failed: <Errors.foo: 1>)

Context()
    """.strip()

    getter = make_collector()
    with pytest.raises(FailureError):
        Q().a()
    assert repr(getter()) == expected

    getter = make_collector()
    Q().a.run()
    assert repr(getter()) == expected

    # Substory DI.

    expected = """
J.a
  before
  x (T.x)
    one (failed: <Errors.foo: 1>)

Context()
    """.strip()

    getter = make_collector()
    with pytest.raises(FailureError):
        J().a()
    assert repr(getter()) == expected

    getter = make_collector()
    J().a.run()
    assert repr(getter()) == expected


def test_context_representation_with_result():

    expected = """
Simple.x
  one
  two
  three (returned: -1)

Context:
  foo: 1  # Story argument
  bar: 3  # Story argument
  baz: 4  # Set by Simple.two
    """.strip()

    getter = make_collector()
    examples.methods.Simple().x(foo=1, bar=3)
    assert repr(getter()) == expected

    getter = make_collector()
    examples.methods.Simple().x.run(foo=1, bar=3)
    assert repr(getter()) == expected

    expected = """
SimpleSubstory.y
  start
  before
  x
    one
    two
    three (returned: -1)

Context:
  spam: 2  # Story argument
  foo: 1   # Set by SimpleSubstory.start
  bar: 3   # Set by SimpleSubstory.before
  baz: 4   # Set by SimpleSubstory.two
    """.strip()

    getter = make_collector()
    examples.methods.SimpleSubstory().y(spam=2)
    assert repr(getter()) == expected

    getter = make_collector()
    examples.methods.SimpleSubstory().y.run(spam=2)
    assert repr(getter()) == expected

    expected = """
SubstoryDI.y
  start
  before
  x (Simple.x)
    one
    two
    three (returned: -1)

Context:
  spam: 2  # Story argument
  foo: 1   # Set by SubstoryDI.start
  bar: 3   # Set by SubstoryDI.before
  baz: 4   # Set by Simple.two
    """.strip()

    getter = make_collector()
    examples.methods.SubstoryDI(examples.methods.Simple().x).y(spam=2)
    assert repr(getter()) == expected

    getter = make_collector()
    examples.methods.SubstoryDI(examples.methods.Simple().x).y.run(spam=2)
    assert repr(getter()) == expected

    expected = """
SubstoryDI.y
  start
  before
  x (Pipe.x)
    one
    two
    three
  after (returned: 6)

Context:
  spam: 3  # Story argument
  foo: 2   # Set by SubstoryDI.start
  bar: 4   # Set by SubstoryDI.before
    """.strip()

    getter = make_collector()
    examples.methods.SubstoryDI(examples.methods.Pipe().x).y(spam=3)
    assert repr(getter()) == expected

    getter = make_collector()
    examples.methods.SubstoryDI(examples.methods.Pipe().x).y.run(spam=3)
    assert repr(getter()) == expected


def test_context_representation_with_skip():

    expected = """
Simple.x
  one
  two (skipped)

Context:
  foo: 1   # Story argument
  bar: -1  # Story argument
    """.strip()

    getter = make_collector()
    examples.methods.Simple().x(foo=1, bar=-1)
    assert repr(getter()) == expected

    getter = make_collector()
    examples.methods.Simple().x.run(foo=1, bar=-1)
    assert repr(getter()) == expected

    expected = """
SimpleSubstory.y
  start
  before
  x
    one
    two (skipped)
  after (returned: -4)

Context:
  spam: -2  # Story argument
  foo: -3   # Set by SimpleSubstory.start
  bar: -1   # Set by SimpleSubstory.before
    """.strip()

    getter = make_collector()
    examples.methods.SimpleSubstory().y(spam=-2)
    assert repr(getter()) == expected

    getter = make_collector()
    examples.methods.SimpleSubstory().y.run(spam=-2)
    assert repr(getter()) == expected

    expected = """
SubstoryDI.y
  start
  before
  x (Simple.x)
    one
    two (skipped)
  after (returned: -4)

Context:
  spam: -2  # Story argument
  foo: -3   # Set by SubstoryDI.start
  bar: -1   # Set by SubstoryDI.before
    """.strip()

    getter = make_collector()
    examples.methods.SubstoryDI(examples.methods.Simple().x).y(spam=-2)
    assert repr(getter()) == expected

    getter = make_collector()
    examples.methods.SubstoryDI(examples.methods.Simple().x).y.run(spam=-2)
    assert repr(getter()) == expected

    expected = """
SubstoryDI.y
  start
  before
  x (SimpleSubstory.z)
    first (skipped)
  after (returned: 4)

Context:
  spam: 2  # Story argument
  foo: 1   # Set by SubstoryDI.start
  bar: 3   # Set by SubstoryDI.before
    """.strip()

    getter = make_collector()
    examples.methods.SubstoryDI(examples.methods.SimpleSubstory().z).y(spam=2)
    assert repr(getter()) == expected

    getter = make_collector()
    examples.methods.SubstoryDI(examples.methods.SimpleSubstory().z).y.run(spam=2)
    assert repr(getter()) == expected


def test_context_representation_with_error():

    expected = """
StepError.x
  one (errored: Exception)

Context()
    """.strip()

    getter = make_collector()
    with pytest.raises(Exception):
        examples.methods.StepError().x()
    assert repr(getter()) == expected

    getter = make_collector()
    with pytest.raises(Exception):
        examples.methods.StepError().x.run()
    assert repr(getter()) == expected


def test_context_representation_with_failure_protocol_error(f):

    expected = """
T.x
  one (errored: FailureProtocolError)

Context()
    """.strip()

    class T(f.ChildWithList, f.WrongMethod):
        pass

    getter = make_collector()
    with pytest.raises(FailureProtocolError):
        T().x()
    assert repr(getter()) == expected

    getter = make_collector()
    with pytest.raises(FailureProtocolError):
        T().x.run()
    assert repr(getter()) == expected


def test_context_representation_with_context_contract_error(m):
    class T(m.ParamChildWithNull, m.StringMethod):
        pass

    class Q(m.ParamParentWithNull, m.NormalParentMethod, T):
        pass

    class J(m.ParamParentWithNull, m.NormalParentMethod):
        def __init__(self):
            self.x = T().x

    # Simple.

    expected = """
T.x
  one (errored: ContextContractError)

Context:
  foo: 1  # Story argument
  bar: 2  # Story argument
    """.strip()

    getter = make_collector()
    with pytest.raises(ContextContractError):
        T().x(foo=1, bar=2)
    assert repr(getter()) == expected

    getter = make_collector()
    with pytest.raises(ContextContractError):
        T().x.run(foo=1, bar=2)
    assert repr(getter()) == expected

    # Substory inheritance.

    expected = """
Q.a
  before
  x
    one (errored: ContextContractError)

Context:
  foo: 1  # Story argument
  bar: 2  # Story argument
    """.strip()

    getter = make_collector()
    with pytest.raises(ContextContractError):
        Q().a(foo=1, bar=2)
    assert repr(getter()) == expected

    getter = make_collector()
    with pytest.raises(ContextContractError):
        Q().a.run(foo=1, bar=2)
    assert repr(getter()) == expected

    # Substory DI.

    expected = """
J.a
  before
  x (T.x)
    one (errored: ContextContractError)

Context:
  foo: 1  # Story argument
  bar: 2  # Story argument
    """.strip()

    getter = make_collector()
    with pytest.raises(ContextContractError):
        J().a(foo=1, bar=2)
    assert repr(getter()) == expected

    getter = make_collector()
    with pytest.raises(ContextContractError):
        J().a.run(foo=1, bar=2)
    assert repr(getter()) == expected


def test_context_representation_with_missing_variables(m):
    class T(m.ParamChildWithNull, m.NormalMethod):
        pass

    class Q(m.ParentWithNull, m.NormalParentMethod, T):
        pass

    class J(m.ParentWithNull, m.NormalParentMethod):
        def __init__(self):
            self.x = T().x

    # Simple.

    expected = """
T.x (errored: ContextContractError)

Context()
    """.strip()

    getter = make_collector()
    with pytest.raises(ContextContractError):
        T().x()
    assert repr(getter()) == expected

    getter = make_collector()
    with pytest.raises(ContextContractError):
        T().x.run()
    assert repr(getter()) == expected

    # Substory inheritance.

    expected = """
Q.a
  before
  x (errored: ContextContractError)

Context()
    """.strip()

    getter = make_collector()
    with pytest.raises(ContextContractError):
        Q().a()
    assert repr(getter()) == expected

    getter = make_collector()
    with pytest.raises(ContextContractError):
        Q().a.run()
    assert repr(getter()) == expected

    # Substory DI.

    expected = """
J.a
  before
  x (T.x) (errored: ContextContractError)

Context()
    """.strip()

    getter = make_collector()
    with pytest.raises(ContextContractError):
        J().a()
    assert repr(getter()) == expected

    getter = make_collector()
    with pytest.raises(ContextContractError):
        J().a.run()
    assert repr(getter()) == expected


def test_context_representation_arguments_order():

    # Simple.

    expected = """
Simple.x
  one
  two
  three (returned: -1)

Context:
  foo: 1  # Story argument
  bar: 3  # Story argument
  baz: 4  # Set by Simple.two
    """.strip()

    getter = make_collector()
    examples.methods.Simple().x(bar=3, foo=1)
    assert repr(getter()) == expected

    getter = make_collector()
    examples.methods.Simple().x.run(bar=3, foo=1)
    assert repr(getter()) == expected

    # FIXME: Substory inheritance.

    # FIXME: Substory DI.


def test_context_representation_long_variable(c):
    class T(c.ParamChild, c.NormalMethod):
        foo = list(range(23))

    class Q(c.ParamParent, c.NormalParentMethod, T):
        pass

    class J(c.ParamParent, c.NormalParentMethod):
        def __init__(self):
            self.x = T().x

    # Simple.

    expected = """
T.x
  one

Context:
  bar: 'baz'  # Story argument
  foo:        # Set by T.one
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22]
    """.strip()

    getter = make_collector()
    T().x(bar="baz")
    assert repr(getter()) == expected

    getter = make_collector()
    T().x.run(bar="baz")
    assert repr(getter()) == expected

    # Substory inheritance.

    expected = """
Q.a
  before
  x
    one
  after

Context:
  bar: 'baz'  # Story argument
  foo:        # Set by Q.one
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22]
    """.strip()

    getter = make_collector()
    Q().a(bar="baz")
    assert repr(getter()) == expected

    getter = make_collector()
    Q().a.run(bar="baz")
    assert repr(getter()) == expected

    # Substory DI.

    expected = """
J.a
  before
  x (T.x)
    one
  after

Context:
  bar: 'baz'  # Story argument
  foo:        # Set by T.one
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22]
    """.strip()

    getter = make_collector()
    J().a(bar="baz")
    assert repr(getter()) == expected

    getter = make_collector()
    J().a.run(bar="baz")
    assert repr(getter()) == expected


def test_context_representation_multiline_variable(c):
    class userlist(list):
        def __repr__(self):
            return "\n ".join(super(userlist, self).__repr__().split())

    class T(c.ParamChild, c.NormalMethod):
        foo = userlist(range(3))

    class Q(c.ParamParent, c.NormalParentMethod, T):
        pass

    class J(c.ParamParent, c.NormalParentMethod):
        def __init__(self):
            self.x = T().x

    # Simple.

    expected = """
T.x
  one

Context:
  bar: 'baz'  # Story argument
  foo:        # Set by T.one
    [0,
     1,
     2]
    """.strip()

    getter = make_collector()
    T().x(bar="baz")
    assert repr(getter()) == expected

    getter = make_collector()
    T().x.run(bar="baz")
    assert repr(getter()) == expected

    # Substory inheritance.

    expected = """
Q.a
  before
  x
    one
  after

Context:
  bar: 'baz'  # Story argument
  foo:        # Set by Q.one
    [0,
     1,
     2]
    """.strip()

    getter = make_collector()
    Q().a(bar="baz")
    assert repr(getter()) == expected

    getter = make_collector()
    Q().a.run(bar="baz")
    assert repr(getter()) == expected

    # Substory DI.

    expected = """
J.a
  before
  x (T.x)
    one
  after

Context:
  bar: 'baz'  # Story argument
  foo:        # Set by T.one
    [0,
     1,
     2]
    """.strip()

    getter = make_collector()
    J().a(bar="baz")
    assert repr(getter()) == expected

    getter = make_collector()
    J().a.run(bar="baz")
    assert repr(getter()) == expected


def test_context_representation_variable_aliases(c):
    class T(c.ParamChild, c.NormalMethod):
        foo = "baz"

    class Q(c.ParamParent, c.NormalParentMethod, T):
        pass

    class J(c.ParamParent, c.NormalParentMethod):
        def __init__(self):
            self.x = T().x

    # Simple.

    expected = """
T.x
  one

Context:
  bar: 'baz'        # Story argument
  foo: `bar` alias  # Set by T.one
    """.strip()

    getter = make_collector()
    T().x(bar=T.foo)
    assert repr(getter()) == expected

    getter = make_collector()
    T().x.run(bar=T.foo)
    assert repr(getter()) == expected

    # Substory inheritance.

    expected = """
Q.a
  before
  x
    one
  after

Context:
  bar: 'baz'        # Story argument
  foo: `bar` alias  # Set by Q.one
    """.strip()

    getter = make_collector()
    Q().a(bar=T.foo)
    assert repr(getter()) == expected

    getter = make_collector()
    Q().a.run(bar=T.foo)
    assert repr(getter()) == expected

    # Substory DI.

    expected = """
J.a
  before
  x (T.x)
    one
  after

Context:
  bar: 'baz'        # Story argument
  foo: `bar` alias  # Set by T.one
    """.strip()

    getter = make_collector()
    J().a(bar=T.foo)
    assert repr(getter()) == expected

    getter = make_collector()
    J().a.run(bar=T.foo)
    assert repr(getter()) == expected
