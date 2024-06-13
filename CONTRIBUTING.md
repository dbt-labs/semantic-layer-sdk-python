# Contributing

Thank you for being interested in contribuiting to the Semantic Layer SDK!

## Submitting code

If you want to contribute by submitting code, this section will explain how to set up the repo and get started.

### Setting up your environment

1. We use [hatch](https://hatch.pypa.io/) as the dependency and environment manager. Make sure you install it via one of the methods described [here](https://hatch.pypa.io/latest/install/). 
2. We use [lefthook](https://github.com/evilmartians/lefthook/) for Git hooks management. The first time you clone the repo, run `lefthook install` to setup the git hooks.

Hatch will manage your environments for you. Check out the list of available environments in [`pyproject.toml`](./pyproject.toml). You probably want to use the `dev` environment by running `hatch shell dev`.


### Committing your changes

Whenever you commit anything, first make sure all git hooks are passing ([ruff](https://github.com/astral-sh/ruff/) and [basedpyright](https://github.com/DetachHead/basedpyright)). Then, write a commit message which follows [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/), and describe well which changes your commit implements. Remember your code will be reviewed by other contributors, so try to keep your commit log fairly organized (but don't stress over it, we squash commits anyways).

Here's

We use [changie](https://changie.dev/) to manage our [`CHANGELOG.md`](./CHANGELOG.md). Please don't edit that file manually.

