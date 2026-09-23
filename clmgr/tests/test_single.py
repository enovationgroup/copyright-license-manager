from clmgr.tests.test_base import run_test_config


def test_single_java():
    run_test_config("default/java/", "Single.java", "default/single.yml")


def test_single_typescript():
    run_test_config("default/ts/", "single.component.ts", "default/single.yml")


def test_single_python():
    run_test_config("default/py/", "single.py", "default/single.yml")


def test_single_dotnet():
    run_test_config("default/cs/", "Single.cs", "default/single.yml")


def test_single_sql():
    run_test_config("default/sql/", "single.sql", "default/single.yml")


def test_format_single_java():
    run_test_config("format/java/", "Single.java", "format/single.yml")


def test_format_single_typescript():
    run_test_config("format/ts/", "single.component.ts", "format/single.yml")


def test_format_single_python():
    run_test_config("format/py/", "single.py", "format/single.yml")


def test_format_single_dotnet():
    run_test_config("format/cs/", "Single.cs", "format/single.yml")


def test_format_single_sql():
    run_test_config("format/sql/", "single.sql", "format/single.yml")


def test_single_javascript():
    run_test_config("default/js/", "single.js", "default/single.yml")


def test_single_css():
    run_test_config("default/css/", "single.css", "default/single.yml")


def test_single_scss():
    run_test_config("default/scss/", "single.scss", "default/single.yml")


def test_single_sass():
    run_test_config("default/sass/", "single.sass", "default/single.yml")


def test_single_html():
    run_test_config("default/html/", "single.html", "default/single.yml")


def test_format_single_javascript():
    run_test_config("format/js/", "single.js", "format/single.yml")


def test_format_single_css():
    run_test_config("format/css/", "single.css", "format/single.yml")


def test_format_single_scss():
    run_test_config("format/scss/", "single.scss", "format/single.yml")


def test_format_single_sass():
    run_test_config("format/sass/", "single.sass", "format/single.yml")


def test_format_single_html():
    run_test_config("format/html/", "single.html", "format/single.yml")
