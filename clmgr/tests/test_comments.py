from clmgr.tests.test_base import run_test_config


def test_comments_java():
    run_test_config("default/java/", "Comments.java", "default/comments.yml")


def test_comments_typescript():
    run_test_config("default/ts/", "comments.component.ts", "default/comments.yml")


def test_comments_python():
    run_test_config("default/py/", "comments.py", "default/comments.yml")


def test_comments_dotnet():
    run_test_config("default/cs/", "Comments.cs", "default/comments.yml")


def test_format_comments_java():
    run_test_config("format/java/", "Comments.java", "format/comments.yml")


def test_format_comments_typescript():
    run_test_config("format/ts/", "comments.component.ts", "format/comments.yml")


def test_format_comments_python():
    run_test_config("format/py/", "comments.py", "format/comments.yml")


def test_format_comments_dotnet():
    run_test_config("format/cs/", "Comments.cs", "format/comments.yml")
