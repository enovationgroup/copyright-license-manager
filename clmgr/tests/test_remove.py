from clmgr.tests.test_base import run_test_config


def test_remove_java():
    run_test_config("default/java/", "Remove.java", "default/remove.yml")


def test_remove_typescript():
    run_test_config("default/ts/", "remove.component.ts", "default/remove.yml")


def test_remove_python():
    run_test_config("default/py/", "remove.py", "default/remove.yml")


def test_remove_dotnet():
    run_test_config("default/cs/", "Remove.cs", "default/remove.yml")


def test_remove_sql():
    run_test_config("default/sql/", "remove.sql", "default/remove.yml")


def test_format_remove_java():
    run_test_config("format/java/", "Remove.java", "format/remove.yml")


def test_format_remove_typescript():
    run_test_config("format/ts/", "remove.component.ts", "format/remove.yml")


def test_format_remove_python():
    run_test_config("format/py/", "remove.py", "format/remove.yml")


def test_format_remove_dotnet():
    run_test_config("format/cs/", "Remove.cs", "format/remove.yml")


def test_format_remove_sql():
    run_test_config("format/sql/", "remove.sql", "format/remove.yml")


def test_remove_javascript():
    run_test_config("default/js/", "remove.js", "default/remove.yml")


def test_remove_css():
    run_test_config("default/css/", "remove.css", "default/remove.yml")


def test_remove_scss():
    run_test_config("default/scss/", "remove.scss", "default/remove.yml")


def test_remove_sass():
    run_test_config("default/sass/", "remove.sass", "default/remove.yml")


def test_remove_html():
    run_test_config("default/html/", "remove.html", "default/remove.yml")


def test_format_remove_javascript():
    run_test_config("format/js/", "remove.js", "format/remove.yml")


def test_format_remove_css():
    run_test_config("format/css/", "remove.css", "format/remove.yml")


def test_format_remove_scss():
    run_test_config("format/scss/", "remove.scss", "format/remove.yml")


def test_format_remove_sass():
    run_test_config("format/sass/", "remove.sass", "format/remove.yml")


def test_format_remove_html():
    run_test_config("format/html/", "remove.html", "format/remove.yml")
