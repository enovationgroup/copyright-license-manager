from clmgr.tests.test_base import run_test_config


def test_single_update_java():
    run_test_config("default/java/", "SingleUpdate.java", "default/single.update.yml")


def test_single_update_typescript():
    run_test_config(
        "default/ts/", "single-update.component.ts", "default/single.update.yml"
    )


def test_single_update_python():
    run_test_config("default/py/", "single_update.py", "default/single.update.yml")


def test_single_update_dotnet():
    run_test_config("default/cs/", "SingleUpdate.cs", "default/single.update.yml")


def test_single_update_sql():
    run_test_config("default/sql/", "single-update.sql", "default/single.update.yml")


def test_format_single_update_java():
    run_test_config("format/java/", "SingleUpdate.java", "format/single.update.yml")


def test_format_single_update_typescript():
    run_test_config(
        "format/ts/", "single-update.component.ts", "format/single.update.yml"
    )


def test_format_single_update_python():
    run_test_config("format/py/", "single_update.py", "format/single.update.yml")


def test_format_single_update_dotnet():
    run_test_config("format/cs/", "SingleUpdate.cs", "format/single.update.yml")


def test_format_single_update_sql():
    run_test_config("format/sql/", "single-update.sql", "format/single.update.yml")


def test_single_update_javascript():
    run_test_config("default/js/", "single-update.js", "default/single.update.yml")


def test_single_update_css():
    run_test_config("default/css/", "single-update.css", "default/single.update.yml")


def test_single_update_scss():
    run_test_config("default/scss/", "single-update.scss", "default/single.update.yml")


def test_single_update_sass():
    run_test_config("default/sass/", "single-update.sass", "default/single.update.yml")


def test_single_update_html():
    run_test_config("default/html/", "single-update.html", "default/single.update.yml")


def test_format_single_update_javascript():
    run_test_config("format/js/", "single-update.js", "format/single.update.yml")


def test_format_single_update_css():
    run_test_config("format/css/", "single-update.css", "format/single.update.yml")


def test_format_single_update_scss():
    run_test_config("format/scss/", "single-update.scss", "format/single.update.yml")


def test_format_single_update_sass():
    run_test_config("format/sass/", "single-update.sass", "format/single.update.yml")


def test_format_single_update_html():
    run_test_config("format/html/", "single-update.html", "format/single.update.yml")


def test_first_line_python():
    run_test_config("default/py/", "first_line.py", "default/single.update.yml")


def test_first_line_sass():
    run_test_config("default/sass/", "first-line.sass", "default/single.update.yml")
