from clmgr.tests.test_base import run_test_config


def test_change_format_java():
    run_test_config("default/java/", "ChangeFormat.java", "default/change-format.yml")


def test_change_format_typescript():
    run_test_config(
        "default/ts/", "change-format.component.ts", "default/change-format.yml"
    )


def test_change_format_python():
    run_test_config("default/py/", "change_format.py", "default/change-format.yml")


def test_change_format_dotnet():
    run_test_config("default/cs/", "ChangeFormat.cs", "default/change-format.yml")


def test_change_format_sql():
    run_test_config("default/sql/", "change-format.sql", "default/change-format.yml")


def test_format_change_format_java():
    run_test_config("format/java/", "ChangeFormat.java", "format/change-format.yml")


def test_format_change_format_typescript():
    run_test_config(
        "format/ts/", "change-format.component.ts", "format/change-format.yml"
    )


def test_format_change_format_python():
    run_test_config("format/py/", "change_format.py", "format/change-format.yml")


def test_format_change_format_dotnet():
    run_test_config("format/cs/", "ChangeFormat.cs", "format/change-format.yml")


def test_format_change_format_sql():
    run_test_config("format/sql/", "change-format.sql", "format/change-format.yml")


def test_change_format_javascript():
    run_test_config("default/js/", "change-format.js", "default/change-format.yml")


def test_change_format_css():
    run_test_config("default/css/", "change-format.css", "default/change-format.yml")


def test_change_format_scss():
    run_test_config("default/scss/", "change-format.scss", "default/change-format.yml")


def test_change_format_sass():
    run_test_config("default/sass/", "change-format.sass", "default/change-format.yml")


def test_change_format_html():
    run_test_config("default/html/", "change-format.html", "default/change-format.yml")


def test_format_change_format_javascript():
    run_test_config("format/js/", "change-format.js", "format/change-format.yml")


def test_format_change_format_css():
    run_test_config("format/css/", "change-format.css", "format/change-format.yml")


def test_format_change_format_scss():
    run_test_config("format/scss/", "change-format.scss", "format/change-format.yml")


def test_format_change_format_sass():
    run_test_config("format/sass/", "change-format.sass", "format/change-format.yml")


def test_format_change_format_html():
    run_test_config("format/html/", "change-format.html", "format/change-format.yml")
