"""A collection of development tasks for this library."""
import invoke


@invoke.task
def generate_docs(ctx, builder="html"):
    """Generate the Sphinx Documentation"""
    ctx.run(f"sphinx-build -M {builder} docs build/docs")
