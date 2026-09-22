import os

from clmgr.paths import matches, select_files


def test_a_pattern_matches_the_relative_path():
    assert matches(["src/main.py"], "src/main.py")
    assert not matches(["src/main.py"], "lib/main.py")


def test_a_single_star_stays_within_one_directory():
    assert matches(["src/*.py"], "src/main.py")
    assert not matches(["src/*.py"], "src/deep/main.py")


def test_a_double_star_crosses_directories():
    assert matches(["src/**/*"], "src/main.py")
    assert matches(["src/**/*"], "src/deep/nested/main.py")
    assert not matches(["src/**/*"], "lib/main.py")


def test_a_leading_double_star_matches_at_any_depth():
    assert matches(["**/*.min.js"], "a.min.js")
    assert matches(["**/*.min.js"], "a/b/c.min.js")
    assert not matches(["**/*.min.js"], "a/b/c.js")


def test_a_bare_name_matches_a_file_name_or_stem():
    assert matches(["Comments"], "src/Comments.java")
    assert matches(["Comments.java"], "src/Comments.java")
    assert not matches(["Comment"], "src/Comments.java")


def test_a_bare_name_matches_a_directory():
    assert matches(["build"], "build/main.py")
    assert matches(["build"], "a/build/main.py")


def test_a_short_name_is_not_matched_by_an_unrelated_pattern():
    """The pattern used to be matched as a substring of a regular expression"""
    for stem in ["s", "Z", "F", "?"]:
        assert not matches(["Foo"], stem + ".py")


def test_no_patterns_match_nothing():
    assert not matches([], "src/main.py")


def test_a_character_class_is_supported():
    assert matches(["main.[ch]"], "main.c")
    assert not matches(["main.[ch]"], "main.o")


def build_tree(tmp_path):
    for path in ["src/a.py", "src/deep/b.py", "src/a.txt", "other/c.py", "build/d.py"]:
        target = tmp_path / path
        os.makedirs(target.parent, exist_ok=True)
        target.write_text("x\n", encoding="utf-8")

    return tmp_path


def relative_names(tmp_path, selected):
    return sorted(str(path.relative_to(tmp_path)) for path in selected)


def test_select_files_filters_on_extension(tmp_path):
    build_tree(tmp_path)
    selected = select_files(tmp_path, "py", [], [])

    assert relative_names(tmp_path, selected) == [
        "build/d.py",
        "other/c.py",
        "src/a.py",
        "src/deep/b.py",
    ]


def test_select_files_applies_include(tmp_path):
    build_tree(tmp_path)
    selected = select_files(tmp_path, "py", ["src/**/*"], [])

    assert relative_names(tmp_path, selected) == ["src/a.py", "src/deep/b.py"]


def test_select_files_applies_exclude(tmp_path):
    build_tree(tmp_path)
    selected = select_files(tmp_path, "py", [], ["build"])

    assert "build/d.py" not in relative_names(tmp_path, selected)


def test_select_files_does_not_descend_into_an_excluded_directory(tmp_path):
    build_tree(tmp_path)
    selected = select_files(tmp_path, "py", [], ["src/deep"])

    assert relative_names(tmp_path, selected) == [
        "build/d.py",
        "other/c.py",
        "src/a.py",
    ]
