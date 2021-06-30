# pylint: disable=redefined-outer-name, unused-argument
import warnings
from contextlib import contextmanager

import boto3
import pytest
from dagster import ExperimentalWarning
from dagster.core.definitions.reconstructable import ReconstructableRepository
from dagster.core.host_representation.origin import InProcessRepositoryLocationOrigin
from dagster.core.test_utils import instance_for_test

from . import repo


@pytest.fixture(autouse=True)
def ignore_experimental_warning():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=ExperimentalWarning)
        yield


@pytest.fixture
def image():
    return "dagster:latest"


@pytest.fixture
def environment():
    return [{"name": "FOO", "value": "bar"}]


@pytest.fixture
def task_definition(ecs, image, environment):
    return ecs.register_task_definition(
        family="dagster",
        containerDefinitions=[
            {
                "name": "dagster",
                "image": image,
                "environment": environment,
            }
        ],
        networkMode="awsvpc",
    )["taskDefinition"]


@pytest.fixture
def task(ecs, network_interface, security_group, task_definition):
    return ecs.run_task(
        taskDefinition=task_definition["family"],
        networkConfiguration={
            "awsvpcConfiguration": {
                "subnets": [network_interface.subnet_id],
                "securityGroups": [security_group.id],
            },
        },
    )["tasks"][0]


@pytest.fixture
def stub_aws(ecs, ec2, monkeypatch):
    # Any call to boto3.client() will return ecs.
    # Any call to boto3.resource() will return ec2.
    # This only works because our launcher happens to use a client for ecs and
    # a resource for ec2 - if that were to change or if new aws objects were to
    # be introduced, this fixture would need to be refactored.
    monkeypatch.setattr(boto3, "client", lambda *args, **kwargs: ecs)
    monkeypatch.setattr(boto3, "resource", lambda *args, **kwargs: ec2)


@pytest.fixture
def stub_ecs_metadata(task, monkeypatch, requests_mock):
    container_uri = "http://metadata_host"
    monkeypatch.setenv("ECS_CONTAINER_METADATA_URI_V4", container_uri)
    container = task["containers"][0]["name"]
    requests_mock.get(container_uri, json={"Name": container})

    task_uri = container_uri + "/task"
    requests_mock.get(
        task_uri,
        json={
            "Cluster": task["clusterArn"],
            "TaskARN": task["taskArn"],
        },
    )


@pytest.fixture
def instance_cm(stub_aws, stub_ecs_metadata):
    @contextmanager
    def cm(config=None):
        overrides = {
            "run_launcher": {
                "module": "dagster_aws.ecs",
                "class": "EcsRunLauncher",
                "config": {**(config or {})},
            }
        }
        with instance_for_test(overrides) as dagster_instance:
            yield dagster_instance

    return cm


@pytest.fixture
def instance(instance_cm):
    with instance_cm() as dagster_instance:
        yield dagster_instance


@pytest.fixture
def pipeline():
    return repo.pipeline


@pytest.fixture
def external_pipeline(image):
    with InProcessRepositoryLocationOrigin(
        ReconstructableRepository.for_file(
            repo.__file__, repo.repository.__name__, container_image=image
        ),
    ).create_location() as location:
        yield location.get_repository(repo.repository.__name__).get_full_external_pipeline(
            repo.pipeline.__name__
        )
