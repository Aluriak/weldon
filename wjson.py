"""Wrapper around json serializer that handle all necessary
classes of weldon project.

"""

import json
from test import Test
from problem import Problem
from commons import custom_json_encoder, custom_json_decoder, SubmissionResult


SERIALIZABLE_CLASSES = (Problem, Test, SubmissionResult)


def from_json(payload:str) -> object or list or dict:
    return json.loads(payload, object_hook=custom_json_decoder(SERIALIZABLE_CLASSES))

def as_json(payload:object or list or dict) -> str:
    return json.dumps(payload, cls=custom_json_encoder(SERIALIZABLE_CLASSES)) + '\n'
