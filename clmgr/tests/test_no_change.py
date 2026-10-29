from clmgr.tests.test_base import run_test_config


def test_no_change_java():
    run_test_config("default/java/", "NoChange.java", "default/no-change.yml")


def test_no_change_typescript():
    run_test_config("default/ts/", "no-change.component.ts", "default/no-change.yml")


def test_no_change_python():
    run_test_config("default/py/", "no_change.py", "default/no-change.yml")


def test_no_change_dotnet():
    run_test_config("default/cs/", "NoChange.cs", "default/no-change.yml")


def test_no_change_sql():
    run_test_config("default/sql/", "no-change.sql", "default/no-change.yml")


def test_format_no_change_java():
    run_test_config("format/java/", "NoChange.java", "format/no-change.yml")


def test_format_no_change_typescript():
    run_test_config("format/ts/", "no-change.component.ts", "format/no-change.yml")


def test_format_no_change_python():
    run_test_config("format/py/", "no_change.py", "format/no-change.yml")


def test_format_no_change_dotnet():
    run_test_config("format/cs/", "NoChange.cs", "format/no-change.yml")


def test_format_no_change_sql():
    run_test_config("format/sql/", "no-change.sql", "format/no-change.yml")


def test_no_change_javascript():
    run_test_config("default/js/", "no-change.js", "default/no-change.yml")


def test_no_change_css():
    run_test_config("default/css/", "no-change.css", "default/no-change.yml")


def test_no_change_scss():
    run_test_config("default/scss/", "no-change.scss", "default/no-change.yml")


def test_no_change_sass():
    run_test_config("default/sass/", "no-change.sass", "default/no-change.yml")


def test_no_change_html():
    run_test_config("default/html/", "no-change.html", "default/no-change.yml")


def test_format_no_change_javascript():
    run_test_config("format/js/", "no-change.js", "format/no-change.yml")


def test_format_no_change_css():
    run_test_config("format/css/", "no-change.css", "format/no-change.yml")


def test_format_no_change_scss():
    run_test_config("format/scss/", "no-change.scss", "format/no-change.yml")


def test_format_no_change_sass():
    run_test_config("format/sass/", "no-change.sass", "format/no-change.yml")


def test_format_no_change_html():
    run_test_config("format/html/", "no-change.html", "format/no-change.yml")
