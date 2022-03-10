from invoke import task


@task
def test_cov(ctx):
    """Run test coverage"""
    ctx.run("pytest --durations 3 -vv --cov-branch --cov devseed --cov-report term")


@task
def publish(ctx):
    """Publish to PyPi"""
    ctx.run("pytest && poetry build && poetry publish")
