# cp-function-testing

First try of writing a Crossplane function in python ([Guide](https://docs.crossplane.io/latest/guides/write-a-composition-function-in-python/#install-the-tools-you-need-to-write-the-function))

## Prerequisites

Install the Tools necessary to write a custom function.

- Python
- Hatch
- Docker
- Crossplane CLI

Initialize the function from a template

```sh
crossplane beta xpkg init function-xbuckets https://github.com/crossplane/function-template-python -d function-xbuckets
```

## Steps

From the template
1. rename the package in `package/crossplane.yaml`
2. write a function logic in `function/fn.py`
3. write a unit test in `tests/test_fn.py`
4. run `hatch run test:unit` in the `function-xbuckets` directory

## Test

Using a composition, a function and a xr file in the `examples` directory, you can test your function locally.
The Function in functions.yaml uses the Development runtime. This tells crossplane beta render that your function is running locally. It connects to your locally running function instead of using Docker to pull and run the function.

`example/composition.yaml`:

```yaml
apiVersion: apiextensions.crossplane.io/v1
kind: Composition
metadata:
  name: create-buckets
spec:
  compositeTypeRef:
    apiVersion: example.crossplane.io/v1
    kind: XBuckets
  mode: Pipeline
  pipeline:
    - step: create-buckets
      functionRef:
        name: function-xbuckets
```

`example/composition.yaml`:

```yaml
apiVersion: pkg.crossplane.io/v1beta1
kind: Function
metadata:
  name: function-xbuckets
  annotations:
    # This tells crossplane beta render to connect to the function locally.
    render.crossplane.io/runtime: Development
spec:
  # This is ignored when using the Development runtime.
  package: function-xbuckets # xpkg.upbound.io/negz/function-xbuckets:v0.1.0
```


`example/xr.yaml`:

```yaml
apiVersion: example.crossplane.io/v1
kind: XR
metadata:
  name: example-xr
spec:
  region: eu-central-1
  names:
    - pe-crossplane-functions-example-a
    - pe-crossplane-functions-example-b
    - pe-crossplane-functions-example-c
```

Then you need to terminals.
In one terminal, you run

```sh
hatch run development
```

In the other you can use crossplane's beta render feature.

```sh
crossplane beta render example/xr.yaml example/composition.yaml example/functions.yaml
```

This command calls your function. In the terminal where your function is running you should now see log output.
The `crossplane beta render` command prints the desired resources the function returns.

```yaml
---
apiVersion: example.crossplane.io/v1
kind: XR
metadata:
  name: example-xr
status:
  conditions:
  - lastTransitionTime: "2024-01-01T00:00:00Z"
    message: 'Unready resources: xbuckets-pe-crossplane-functions-example-a, xbuckets-pe-crossplane-functions-example-b,
      and xbuckets-pe-crossplane-functions-example-c'
    reason: Creating
    status: "False"
    type: Ready
---
apiVersion: s3.aws.upbound.io/v1beta1
kind: Bucket
metadata:
  annotations:
    crossplane.io/composition-resource-name: xbuckets-pe-crossplane-functions-example-a
    crossplane.io/external-name: pe-crossplane-functions-example-a
  generateName: example-xr-
  labels:
    crossplane.io/composite: example-xr
  ownerReferences:
  - apiVersion: example.crossplane.io/v1
    blockOwnerDeletion: true
    controller: true
    kind: XR
    name: example-xr
    uid: ""
spec:
  forProvider:
    region: eu-central-1
---
apiVersion: s3.aws.upbound.io/v1beta1
kind: Bucket
metadata:
  annotations:
    crossplane.io/composition-resource-name: xbuckets-pe-crossplane-functions-example-b
    crossplane.io/external-name: pe-crossplane-functions-example-b
  generateName: example-xr-
  labels:
    crossplane.io/composite: example-xr
  ownerReferences:
  - apiVersion: example.crossplane.io/v1
    blockOwnerDeletion: true
    controller: true
    kind: XR
    name: example-xr
    uid: ""
spec:
  forProvider:
    region: eu-central-1
---
apiVersion: s3.aws.upbound.io/v1beta1
kind: Bucket
metadata:
  annotations:
    crossplane.io/composition-resource-name: xbuckets-pe-crossplane-functions-example-c
    crossplane.io/external-name: pe-crossplane-functions-example-c
  generateName: example-xr-
  labels:
    crossplane.io/composite: example-xr
  ownerReferences:
  - apiVersion: example.crossplane.io/v1
    blockOwnerDeletion: true
    controller: true
    kind: XR
    name: example-xr
    uid: ""
spec:
  forProvider:
    region: eu-central-1
```

## Build and Push

You build a function in two stages. First you build the function’s runtime. This is the Open Container Initiative (OCI) image Crossplane uses to run your function. You then embed that runtime in a package, and push it to a package registry. The Crossplane CLI uses `xpkg.upbound.io` as its default package registry.

A function supports a single platform, like linux/amd64, by default. You can support multiple platforms by building a runtime and package for each platform, then pushing all the packages to a single tag in the registry.

```sh
docker build . --quiet --platform=linux/amd64 --tag runtime-amd64
docker build . --quiet --platform=linux/arm64 --tag runtime-arm64
```

Use the Crossplane CLI to build a package for each platform. Each package embeds a runtime image.

The` --package-root` flag specifies the `package` directory, which contains `crossplane.yaml`. This includes metadata about the package.

The `--embed-runtime-image` flag specifies the runtime image tag built using Docker.

The `--package-file` flag specifies specifies where to write the package file to disk. Crossplane package files use the extension .xpkg.

```sh
crossplane xpkg build \
    --package-root=package \
    --embed-runtime-image=runtime-amd64 \
    --package-file=function-amd64.xpkg
---
crossplane xpkg build \
    --package-root=package \
    --embed-runtime-image=runtime-arm64 \
    --package-file=function-arm64.xpkg
```

Push both package files to a registry. Pushing both files to one tag in the registry creates a multi-platform package that runs on both linux/arm64 and linux/amd64 hosts.

```sh
crossplane xpkg push \
  --package-files=function-amd64.xpkg,function-arm64.xpkg \
  negz/function-xbuckets:v0.1.0
```
