# Python (and development) for a Java QA automation engineer

**Who the owner is.** A senior QA automation engineer, not a developer by trade. Strong in Java and Spring as used in test automation, and strong in testing itself: test design, fixtures, assertions, CI, finding edge cases. Less fluent in Python, in application design (architecture, layering, dependency injection, data modelling, concurrency, packaging and deployment) and in UI work (ADR 0011).

The code stays in Python because the analytics and the UI are much cheaper in Python. The cost of that choice is paid here: the code is written so the owner can review, debug and extend it, and anything unfamiliar is explained as it comes up.

## 1. Explaining as we go

Three kinds of things get explained, each briefly, the first time they appear:

- **Python idioms** that differ from Java (§2–§4).
- **Development and design concepts** that a test automation engineer may not use day to day: why a layer or interface exists, dependency injection, idempotency, migrations, caching, retries and backoff, concurrency, packaging, launchd. Say what the concept is, why this code needs it, and what would go wrong without it.
- **UI concepts:** how Streamlit works (the whole script reruns top to bottom on every interaction; `st.session_state` keeps values between reruns; `st.cache_data` caches results), layout (columns, tabs, containers), forms and widgets, and basic usability choices (what goes first on a page, when to use a table versus a chart). Before building a page, sketch it in plain words or ASCII so the owner can react to the layout before any code exists.

How:

- **Connect to testing where possible.** It's the owner's home ground: a Protocol plus a fake is "the seam you'd want for testing", the `as_of` parameter is "a controllable clock", and pure parsers over recorded files are "golden-file tests". Ask for their review of test design; that's where their judgment is strongest.
- When code in a change uses a Python idiom a Java reader would not read at a glance, explain it in the reply: one or two sentences, with the Java equivalent where one exists. Example: "`@dataclass(frozen=True)` is Python's `record`: it generates the constructor, `equals`, `hashCode` and `toString`, and makes fields read-only."
- Explain each idiom or concept once. After explaining one, add it to §5 (Explained so far) in the same change, so later sessions don't repeat it. When an idiom in §5 appears in an unusual way, a short reminder is fine.
- Don't explain general programming, basic Python syntax (loops, functions, imports) or testing practice. Focus on what differs from Java, on application design, and on UI.
- When summarising a change, add a short **Notes** section (Python, design or UI) if the change introduced something new.
- When the owner asks "why is it written like this?", answer with the trade-off, not only the rule.

## 2. Typing rules

`pyright` runs in **strict** mode on `src/` and `tests/` (`pyproject.toml`). Type checking happens only in the checker, never at runtime: Python runs badly typed code without complaint. That makes pyright the equivalent of `javac`, and it must pass before work counts as done.

- Every function has parameter and return annotations, including tests (`-> None`) and fixtures.
- **No `Any`**, except at a boundary that really is untyped: `json.loads`, a library without stubs, a pandas cell. Give the value a real type right there (a `TypedDict`, a dataclass, or the `Json` alias in `nfa.devtools.scrub`) and don't let `Any` travel.
- `X | None` for nullable values. The checker forces a `None` check before use, like a strict `Optional<T>`.
- Parameters take read-only abstract types (`Sequence[T]`, `Mapping[K, V]`, `Iterable[T]` from `collections.abc`). Return values use concrete types (`list[T]`, `dict[K, V]`). It's the same rule as accepting `List<T>` and returning `ArrayList<T>`, plus read-only intent.
- IDs are `NewType`s (`PlayerId = NewType("PlayerId", str)`), so a team key can't be passed where a player ID is expected.
- Fixed vocabularies are `Enum` or `StrEnum`, never bare strings.
- Every `# pyright: ignore[ruleName]` names the rule and has a reason on the same line. A bare `# type: ignore` is not allowed.

## 3. Plain, Java-like style

- **Interfaces are `typing.Protocol`s** in `domain/interfaces.py`; implementations are ordinary classes in `adapters/`.
- **Constructor injection.** A class receives its collaborators in `__init__`. It never creates them itself and never reaches for globals. `nfa/wiring.py` is the hand-written equivalent of a Spring `@Configuration` class: the only place concrete adapters are built and connected. There is no DI framework.
- **Value objects are frozen dataclasses**, Python's `record`. Validation goes in `__post_init__`, like a compact canonical constructor.
- **No magic:** no metaclasses, no `__getattr__` tricks, no monkeypatching outside tests, and no decorators except `dataclass`, `property`, `staticmethod`, `classmethod`, `override` and pytest's. Comprehensions are fine while they fit on one or two lines; otherwise use a loop.
- **Exceptions:** each module defines its own exception classes (`AuthError`, `FetchError`). Python has no checked exceptions, so a public function that raises documents it in its docstring.
- `_name` marks a module or class member as private. Nothing enforces it, so treat it as `private` anyway.

## 4. Java ↔ Python map

| Java / Spring | Here | Note |
|---|---|---|
| `interface` + `implements` | `typing.Protocol` | Structural: a class satisfies it by having the methods. There's no `implements`; pyright checks it at the point of use. |
| `record` / Lombok `@Value` | `@dataclass(frozen=True)` | Generates the constructor, `equals`, `hashCode` and `toString` (`__init__`, `__eq__`, `__hash__`, `__repr__`). |
| `enum` | `Enum`, `StrEnum` | `StrEnum` members are also strings, which is handy for JSON and SQL. |
| `Optional<T>` / `null` | `T \| None` / `None` | |
| Generics `List<T>` | `list[T]`; `def first[T](xs: Sequence[T]) -> T` | Python 3.12 syntax for generic functions and classes. Generics are invariant, as in Java (§5). |
| `@Override` | `@override` (`typing`) | Optional, but use it in adapters. |
| Package / class per file | Package = folder with `__init__.py`; module = file | A module can hold several small classes and functions. |
| Spring `@Configuration`, `@Bean` | `nfa/wiring.py` factory functions | Explicit, no annotations. |
| `@Scheduled` | launchd runs `python -m nfa.jobs.daily` | There's no long-running process. |
| `application.yml` | `config.toml` + `nfa/config.py` | Secrets stay in the Keychain. |
| Maven / Gradle, `pom.xml` | `uv`, `pyproject.toml`, `uv.lock` | `uv sync` is roughly `mvn install`; `uv run X` runs X inside the project's environment. |
| Checkstyle / Spotless | `ruff check`, `ruff format` | |
| `javac` type errors | `pyright` | Separate step; runtime does not check. |
| JUnit test class | Plain `test_*` functions in `tests/` | `assert x == y` replaces `assertEquals`, and pytest shows both sides on failure. |
| `@BeforeEach`, test DI | pytest fixtures | A fixture is a function. A test receives it by naming it as a parameter. `yield` in a fixture separates setup from teardown. |
| `@ParameterizedTest` | `@pytest.mark.parametrize` | |
| Mockito | Hand-written fakes in `tests/fakes.py` | Preferred over mocks: a fake implements the Protocol, so pyright checks it. |
| try-with-resources | `with` | |
| Streams | Comprehensions and generators | `[f(x) for x in xs if p(x)]` is `xs.stream().filter(p).map(f).toList()`. |
| `String.format` | f-strings: `f"{name}: {value:.3f}"` | |

**Behavior that surprises Java developers:**
- **Annotations are not enforced at runtime.** `def f(x: int)` accepts a string if called that way. Only pyright catches it.
- **Mutable default arguments are shared between calls.** `def f(xs: list[int] = [])` reuses one list forever. Use `None`, or `field(default_factory=...)` in dataclasses.
- **Truthiness.** `0`, `0.0`, `""`, `[]` and `None` are all false in `if x:`. A stat of 0 blocks is falsy, so test `if x is None:` when you mean "missing".
- **`/` is always float division**; `//` is floor division.
- **`is` compares identity, `==` compares equality** (like `==` versus `.equals`). Use `is` only for `None`.
- **Dicts keep insertion order**, which is guaranteed.
- **Naive vs aware datetimes.** A `datetime` without a timezone is a "naive" one, like `LocalDateTime`. This code base allows only timezone-aware ones (`ZonedDateTime`), and `nfa.clock` is the only module that reads the real time.

## 5. Explained so far

One line each, under the matching heading. Add a line in the same change that first explains something.

### Python

- **`type Json = None | bool | int | float | str | list[Json] | dict[str, Json]`:** the Python 3.12 `type` statement declares a type alias, which can refer to itself. Here it's the shape of any parsed JSON. Code that receives a `Json` must narrow it (`isinstance(obj, dict)`) before indexing it, like `instanceof` with pattern matching.
- **Invariance:** a `dict[str, int]` is not a `dict[str, Json]`, for the same reason a `List<Integer>` is not a `List<Object>`. Annotate the variable (`data: Json = {...}`) so the literal is built as the wider type.
- **`field(default_factory=dict[str, str])`:** a dataclass field's default is created fresh for each instance, which avoids the shared-mutable-default problem. Passing the typed `dict[str, str]` tells pyright the element types.
- **`Iterator[T]` return type on a `yield` fixture:** a function containing `yield` is a generator. pytest runs it up to `yield` (setup), hands the yielded value to the test, then runs the rest (teardown).

### Design

(none yet)

### UI

(none yet)
