from invoke import task


@task
def test_cov(ctx):
    """Run test coverage"""
    ctx.run("pytest --durations 3 -vv --cov-branch --cov devseed --cov-report term")


@task
def version(ctx, dry_run=False):
    """Bump version"""
    cmd = "bumpver update"
    if dry_run:
        cmd += " --dry"
    ctx.run(cmd)
