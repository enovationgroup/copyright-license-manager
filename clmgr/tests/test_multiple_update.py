from clmgr.tests.test_base import run_test_config


def test_multiple_update_java():
    run_test_config(
        "default/java/", "MultipleUpdate.java", "default/multiple.update.yml"
    )


def test_multiple_update_typescript():
    run_test_config(
        "default/ts/", "multiple-update.component.ts", "default/multiple.update.yml"
    )


def test_multiple_update_python():
    run_test_config("default/py/", "multiple_update.py", "default/multiple.update.yml")


def test_multiple_dotnet():
    run_test_config("default/cs/", "MultipleUpdate.cs", "default/multiple.update.yml")


def test_multiple_update_sql():
    run_test_config(
        "default/sql/", "multiple-update.sql", "default/multiple.update.yml"
    )


def test_format_multiple_update_java():
    run_test_config("format/java/", "MultipleUpdate.java", "format/multiple.update.yml")


def test_format_multiple_update_typescript():
    run_test_config(
        "format/ts/", "multiple-update.component.ts", "format/multiple.update.yml"
    )


def test_format_multiple_update_python():
    run_test_config("format/py/", "multiple_update.py", "format/multiple.update.yml")


def test_format_multiple_dotnet():
    run_test_config("format/cs/", "MultipleUpdate.cs", "format/multiple.update.yml")


def test_format_multiple_update_sql():
    run_test_config("format/sql/", "multiple-update.sql", "format/multiple.update.yml")


def test_multiple_update_javascript():
    run_test_config("default/js/", "multiple-update.js", "default/multiple.update.yml")


def test_multiple_update_css():
    run_test_config(
        "default/css/", "multiple-update.css", "default/multiple.update.yml"
    )


def test_multiple_update_scss():
    run_test_config(
        "default/scss/", "multiple-update.scss", "default/multiple.update.yml"
    )


def test_multiple_update_sass():
    run_test_config(
        "default/sass/", "multiple-update.sass", "default/multiple.update.yml"
    )


def test_multiple_update_html():
    run_test_config(
        "default/html/", "multiple-update.html", "default/multiple.update.yml"
    )


def test_format_multiple_update_javascript():
    run_test_config("format/js/", "multiple-update.js", "format/multiple.update.yml")


def test_format_multiple_update_css():
    run_test_config("format/css/", "multiple-update.css", "format/multiple.update.yml")


def test_format_multiple_update_scss():
    run_test_config(
        "format/scss/", "multiple-update.scss", "format/multiple.update.yml"
    )


def test_format_multiple_update_sass():
    run_test_config(
        "format/sass/", "multiple-update.sass", "format/multiple.update.yml"
    )


def test_format_multiple_update_html():
    run_test_config(
        "format/html/", "multiple-update.html", "format/multiple.update.yml"
    )
