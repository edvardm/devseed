from invoke import task


@task
def test_cov(c):
    """Run test coverage"""
    c.run("pytest --durations 3 -vv --cov-branch --cov devseed --cov-report term")


@task
def test(c):
    """Run tests"""
    c.run("pytest --color yes tests/")


@task(pre=[test])
def publish(c):
    """Publish to PyPi"""
    c.run("poetry build && poetry publish")
