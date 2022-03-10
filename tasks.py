from invoke import task


@task
def test_cov(ctx):
    """Run test coverage"""
    ctx.run("pytest --durations 3 -vv --cov-branch --cov devseed --cov-report term")


@task
def minor(ctx, dry_run=False):
    """Bump minor version"""
    cmd = ["bumpver update --minor"]
    if dry_run:
        cmd += "--dry"

    ctx.run(" ".join(cmd))

@task
def patch(ctx, dry_run=False):
    """Bump version"""
    cmd = ["bumpver update --patch"]
    if dry_run:
        cmd += "--dry"

    ctx.run(cmd)
