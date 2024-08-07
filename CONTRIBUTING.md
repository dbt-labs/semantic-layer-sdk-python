# Contributing

Thank you for being interested in contribuiting to the Semantic Layer SDK!

There are many ways you can contribute to this project.


## Submitting an issue

If you feel like your use case hasn't been covered by the SDK, or if you found a bug or regression, please open an issue to this repo. Try to include as much detail as possible.


## Submitting code

If you want to contribute by submitting code, this section will explain how to set up the repo and get started.


### Setting up your environment

1. We use [hatch](https://hatch.pypa.io/) as the dependency and environment manager. Make sure you install it via one of the methods described [here](https://hatch.pypa.io/latest/install/). 
2. We use [lefthook](https://github.com/evilmartians/lefthook/) for Git hooks management. The first time you clone the repo, run `lefthook install` to setup the git hooks.

Hatch will manage your environments for you. Check out the list of available environments in [`pyproject.toml`](./pyproject.toml). Here follows a brief explanation of what they are for:
- `default`: run only basic scripts, no dependencies installed
- `test`: SDK and test dependencies installed
- `pypi-test-*`: install the SDK from `https://test.pypi.org/simple/` to make sure our build and publish pipelines work before actually publishing the real package
- `dev`: install SDK dependencies and other tools needed during dev such as `ruff` and `basedpyright`.

For most use cases, you probably want to use the `dev` environment by running `hatch shell dev`.

If you're having problems with your environment, check out the [troubleshooting](#troubleshooting) section.


### Upgrading dependencies

If you want to upgrade, remove or add a dependency, change the `pyproject.toml` file. Make sure to include a reasonable min/max version range to facilitate installation by end users. Also make sure the entire test matrix passes.


### Making code changes

Try to keep your code clean and organized. Write documentation to public methods, and write appropriate tests.

We use [changie](https://changie.dev/) to manage our [`CHANGELOG.md`](./CHANGELOG.md). Please don't edit that file manually.


### Running tests

Run tests by using `hatch run test:all`. This will run all our tests in all supported Python versions and with a variety of dependency versions. Make sure they pass before you submit a PR.

If you want to run unit test separately, run `hatch run test:unit`. For integration tests, run `hatch run test.py3.12-highest:integration` to avoid running slow tests in all python versions.

The unit test suite requires a `tests/server_schema.gql` file to exist, since it checks that all GraphQL queries from the SDK will work against the server. That file must contain the schema of the GraphQL API, and you can obtain it by running our introspection script with `hatch run dev:fetch-schema`.

The integration test suite requires an actual Semantic Layer account. Make sure you have `SL_HOST`, `SL_TOKEN` and `SL_ENV_ID` set as environment variables before running.


### Committing changes

Whenever you commit anything, first make sure all git hooks are passing ([ruff](https://github.com/astral-sh/ruff/) and [basedpyright](https://github.com/DetachHead/basedpyright)). Then, write a commit message which follows [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/), and describe well which changes your commit implements. Remember your code will be reviewed by other contributors, so try to keep your commit log fairly organized (but don't stress over it, we squash pull-requests anyways).

We don't require every commit to be perfect, but your pull-request as a whole must pass formatter and linter checks, pass all tests and be appropriately documented.


## Vulnerability disclosure

If you think you've found a security vulnerability (i.e something that could leak customer data, compromise API keys, gain access to unauthorized resources), **do not open an issue in GitHub**. In that case, contact us directly at `security@dbtlabs.com`, and wait until the vulnerability has been patched before publicly disclosing it.


## Troubleshooting

Here's a non-exhaustive list of problems that might occur during development.

### `clang: error: the clang compiler does not support 'faltivec', please use -maltivec and include altivec.h explicitly`

For compatibility issues, we support older versions of libraries such as PyArrow. However, those older versions might not compile properly in MacOS with the error above. This issue might arise especially when running tests in the environment with older versions.

To solve it, you need to install [OpenBLAS](https://www.openblas.net/) and tell the compiler where it is:
```
brew install openblas
export OPENBLAS=$(brew --prefix openblas)
```
