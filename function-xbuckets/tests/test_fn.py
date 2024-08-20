import dataclasses
import unittest

from crossplane.function import logging, resource
from crossplane.function.proto.v1beta1 import run_function_pb2 as fnv1beta1
from google.protobuf import duration_pb2 as durationpb
from google.protobuf import json_format
from google.protobuf import struct_pb2 as structpb

from function import fn


class TestFunctionRunner(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        logging.configure(level=logging.Level.DISABLED)
        self.maxDiff = 2000

    async def test_run_function(self) -> None:
        @dataclasses.dataclass
        class TestCase:
            reason: str
            req: fnv1beta1.RunFunctionRequest
            want: fnv1beta1.RunFunctionResponse

        cases = [
            TestCase(
                reason="The function should compose two S3 buckets.",
                req=fnv1beta1.RunFunctionRequest(
                    observed=fnv1beta1.State(
                        composite=fnv1beta1.Resource(
                            resource=resource.dict_to_struct(
                                {
                                    "apiVersion": "example.crossplane.io/v1alpha1",
                                    "kind": "XBuckets",
                                    "metadata": {"name": "test"},
                                    "spec": {
                                        "region": "us-east-2",
                                        "names": ["test-bucket-a", "test-bucket-b"],
                                    },
                                }
                            )
                        )
                    )
                ),
                want=fnv1beta1.RunFunctionResponse(
                    meta=fnv1beta1.ResponseMeta(ttl=durationpb.Duration(seconds=60)),
                    desired=fnv1beta1.State(
                        resources={
                            "xbuckets-test-bucket-a": fnv1beta1.Resource(
                                resource=resource.dict_to_struct(
                                    {
                                        "apiVersion": "s3.aws.upbound.io/v1beta1",
                                        "kind": "Bucket",
                                        "metadata": {
                                            "annotations": {
                                                "crossplane.io/external-name": "test-bucket-a"
                                            },
                                        },
                                        "spec": {
                                            "forProvider": {"region": "us-east-2"}
                                        },
                                    }
                                )
                            ),
                            "xbuckets-test-bucket-b": fnv1beta1.Resource(
                                resource=resource.dict_to_struct(
                                    {
                                        "apiVersion": "s3.aws.upbound.io/v1beta1",
                                        "kind": "Bucket",
                                        "metadata": {
                                            "annotations": {
                                                "crossplane.io/external-name": "test-bucket-b"
                                            },
                                        },
                                        "spec": {
                                            "forProvider": {"region": "us-east-2"}
                                        },
                                    }
                                )
                            ),
                        },
                    ),
                    context=structpb.Struct(),
                ),
            ),
        ]

        runner = fn.FunctionRunner()

        for case in cases:
            got = await runner.RunFunction(case.req, None)
            self.assertEqual(
                json_format.MessageToDict(got),
                json_format.MessageToDict(case.want),
                "-want, +got",
            )


if __name__ == "__main__":
    unittest.main()