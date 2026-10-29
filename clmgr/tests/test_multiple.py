from clmgr.tests.test_base import run_test_config


def test_multiple_java():
    run_test_config("default/java/", "Multiple.java", "default/multiple.yml")


def test_multiple_typescript():
    run_test_config("default/ts/", "multiple.component.ts", "default/multiple.yml")


def test_multiple_python():
    run_test_config("default/py/", "multiple.py", "default/multiple.yml")


def test_multiple_dotnet():
    run_test_config("default/cs/", "Multiple.cs", "default/multiple.yml")


def test_multiple_sql():
    run_test_config("default/sql/", "multiple.sql", "default/multiple.yml")


def test_format_multiple_java():
    run_test_config("format/java/", "Multiple.java", "format/multiple.yml")


def test_format_multiple_typescript():
    run_test_config("format/ts/", "multiple.component.ts", "format/multiple.yml")


def test_format_multiple_python():
    run_test_config("format/py/", "multiple.py", "format/multiple.yml")


def test_format_multiple_dotnet():
    run_test_config("format/cs/", "Multiple.cs", "format/multiple.yml")


def test_format_multiple_sql():
    run_test_config("format/sql/", "multiple.sql", "format/multiple.yml")


def test_multiple_javascript():
    run_test_config("default/js/", "multiple.js", "default/multiple.yml")


def test_multiple_css():
    run_test_config("default/css/", "multiple.css", "default/multiple.yml")


def test_multiple_scss():
    run_test_config("default/scss/", "multiple.scss", "default/multiple.yml")


def test_multiple_sass():
    run_test_config("default/sass/", "multiple.sass", "default/multiple.yml")


def test_multiple_html():
    run_test_config("default/html/", "multiple.html", "default/multiple.yml")


def test_format_multiple_javascript():
    run_test_config("format/js/", "multiple.js", "format/multiple.yml")


def test_format_multiple_css():
    run_test_config("format/css/", "multiple.css", "format/multiple.yml")


def test_format_multiple_scss():
    run_test_config("format/scss/", "multiple.scss", "format/multiple.yml")


def test_format_multiple_sass():
    run_test_config("format/sass/", "multiple.sass", "format/multiple.yml")


def test_format_multiple_html():
    run_test_config("format/html/", "multiple.html", "format/multiple.yml")
