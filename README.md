# cp-function-testing

First try of writing a Crossplane function in python ([Guide](https://docs.crossplane.io/latest/guides/write-a-composition-function-in-python/#install-the-tools-you-need-to-write-the-function))

## Prerequisites

Install the Tools necessary to write a custom function.

- Python
- Hatch
- Docker
- Crossplane CLI

## Steps

Initialize the function from a template

```sh
crossplane beta xpkg init function-xbuckets https://github.com/crossplane/function-template-python -d function-xbuckets
```