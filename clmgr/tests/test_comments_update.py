from clmgr.tests.test_base import run_test_config


def test_comments_update_java():
    run_test_config("default/java/", "CommentsUpdate.java", "default/comments.yml")


def test_comments_update_typescript():
    run_test_config(
        "default/ts/", "comments-update.component.ts", "default/comments.yml"
    )


def test_comments_update_python():
    run_test_config("default/py/", "comments_update.py", "default/comments.yml")


def test_comments_update_dotnet():
    run_test_config("default/cs/", "CommentsUpdate.cs", "default/comments.yml")


def test_comments_update_sql():
    run_test_config("default/sql/", "comments-update.sql", "default/comments.yml")


def test_format_comments_update_java():
    run_test_config("format/java/", "CommentsUpdate.java", "format/comments.yml")


def test_format_comments_update_typescript():
    run_test_config("format/ts/", "comments-update.component.ts", "format/comments.yml")


def test_format_comments_update_python():
    run_test_config("format/py/", "comments_update.py", "format/comments.yml")


def test_format_comments_update_dotnet():
    run_test_config("format/cs/", "CommentsUpdate.cs", "format/comments.yml")


def test_format_comments_update_sql():
    run_test_config("format/sql/", "comments-update.sql", "format/comments.yml")
