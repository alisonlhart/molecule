#  Copyright (c) 2015-2018 Cisco Systems, Inc.  # noqa: D100
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to
#  deal in the Software without restriction, including without limitation the
#  rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
#  sell copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#  DEALINGS IN THE SOFTWARE.

import collections
import os

from pathlib import Path
from typing import Any

import pytest

from pytest_mock import MockerFixture

from molecule import config, util
from molecule.provisioner import ansible, ansible_playbooks
from tests.unit.conftest import os_split  # pylint:disable=C0411


@pytest.fixture()
def _patched_ansible_playbook(mocker):  # type: ignore[no-untyped-def]  # noqa: ANN001, ANN202, PT005
    m = mocker.patch("molecule.provisioner.ansible_playbook.AnsiblePlaybook")
    m.return_value.execute.return_value = b"patched-ansible-playbook-stdout"

    return m


@pytest.fixture()
def _patched_write_inventory(mocker):  # type: ignore[no-untyped-def]  # noqa: ANN001, ANN202, PT005
    return mocker.patch("molecule.provisioner.ansible.Ansible._write_inventory")


@pytest.fixture()
def _patched_remove_vars(mocker):  # type: ignore[no-untyped-def]  # noqa: ANN001, ANN202, PT005
    return mocker.patch("molecule.provisioner.ansible.Ansible._remove_vars")


@pytest.fixture()
def _patched_link_or_update_vars(mocker):  # type: ignore[no-untyped-def]  # noqa: ANN001, ANN202, PT005
    return mocker.patch("molecule.provisioner.ansible.Ansible._link_or_update_vars")


@pytest.fixture()
def _provisioner_section_data():  # type: ignore[no-untyped-def]  # noqa: ANN202, PT005
    return {
        "provisioner": {
            "name": "ansible",
            "config_options": {"defaults": {"foo": "bar"}},
            "connection_options": {"foo": "bar"},
            "options": {"foo": "bar", "become": True, "v": True},
            "env": {
                "FOO": "bar",
                "ANSIBLE_ROLES_PATH": "foo/bar",
                "ANSIBLE_LIBRARY": "foo/bar",
                "ANSIBLE_FILTER_PLUGINS": "foo/bar",
            },
            "inventory": {
                "hosts": {
                    "all": {
                        "hosts": {"extra-host-01": {}},
                        "children": {"extra-group": {"hosts": ["extra-host-01"]}},
                    },
                },
                "host_vars": {
                    "instance-1": [{"foo": "bar"}],
                    "localhost": [{"foo": "baz"}],
                },
                "group_vars": {
                    "example_group1": [{"foo": "bar"}],
                    "example_group2": [{"foo": "bar"}],
                },
            },
        },
    }


@pytest.fixture(name="instance")
def fixture_instance(
    _provisioner_section_data: dict[str, Any],
    config_instance: config.Config,
) -> ansible.Ansible:
    """Create a provisioner instance.

    Args:
        _provisioner_section_data: A dictionary containing the provisioner section data.
        config_instance: An instance of a Molecule config.
    """
    return ansible.Ansible(config_instance)


def test_profisioner_config_private_member(instance):  # type: ignore[no-untyped-def]  # noqa: ANN001, ANN201, D103
    assert isinstance(instance._config, config.Config)


def test_default_config_options_property(instance):  # type: ignore[no-untyped-def]  # noqa: ANN001, ANN201, D103
    x = {
        "defaults": {
            "ansible_managed": "Ansible managed: Do NOT edit this file manually!",
            "display_failed_stderr": True,
            "forks": 50,
            "host_key_checking": False,
            # https://docs.ansible.com/ansible/devel/reference_appendices/interpreter_discovery.html
            "interpreter_python": "auto_silent",
            "nocows": 1,
            "retry_files_enabled": False,
        },
        "ssh_connection": {
            "control_path": "%(directory)s/%%h-%%p-%%r",
            "scp_if_ssh": True,
        },
    }

    assert x == instance.default_config_options


def test_provisioner_default_options_property(instance):  # type: ignore[no-untyped-def]  # noqa: ANN001, ANN201, D103
    assert {"skip-tags": "molecule-notest,notest"} == instance.default_options


def test_ansible_default_env_property(instance):  # type: ignore[no-untyped-def]  # noqa: ANN001, ANN201, D103
    x = instance._config.provisioner.config_file

    assert x == instance.default_env["ANSIBLE_CONFIG"]
    assert "MOLECULE_FILE" in instance.default_env
    assert "MOLECULE_INVENTORY_FILE" in instance.default_env
    assert "MOLECULE_SCENARIO_DIRECTORY" in instance.default_env
    assert "MOLECULE_INSTANCE_CONFIG" in instance.default_env
    assert "ANSIBLE_CONFIG" in instance.env
    assert "ANSIBLE_ROLES_PATH" in instance.env
    assert "ANSIBLE_LIBRARY" in instance.env
    assert "ANSIBLE_FILTER_PLUGINS" in instance.env


def test_provisioner_name_property(instance):  # type: ignore[no-untyped-def]  # noqa: ANN001, ANN201, D103
    assert instance.name == "ansible"


@pytest.mark.parametrize(
    "config_instance",
    ["_provisioner_section_data"],  # noqa: PT007
    indirect=True,
)
def test_config_options_property(instance):  # type: ignore[no-untyped-def]  # noqa: ANN001, ANN201, D103
    x = {
        "defaults": {
            "ansible_managed": "Ansible managed: Do NOT edit this file manually!",
            "display_failed_stderr": True,
            "foo": "bar",
            "forks": 50,
            "host_key_checking": False,
            "interpreter_python": "auto_silent",
            "nocows": 1,
            "retry_files_enabled": False,
        },
        "ssh_connection": {
            "control_path": "%(directory)s/%%h-%%p-%%r",
            "scp_if_ssh": True,
        },
    }

    assert x == instance.config_options


@pytest.mark.parametrize(
    "config_instance",
    ["_provisioner_section_data"],  # noqa: PT007
    indirect=True,
)
def test_ansible_options_property(instance):  # type: ignore[no-untyped-def]  # noqa: ANN001, ANN201, D103
    x = {"become": True, "foo": "bar", "v": True, "skip-tags": "molecule-notest,notest"}

    assert x == instance.options


def test_ansible_options_property_does_not_merge(instance):  # type: ignore[no-untyped-def]  # noqa: ANN001, ANN201, D103
    for action in ["create", "destroy"]:
        instance._config.action = action

        assert {"skip-tags": "molecule-notest,notest"} == instance.options


def test_provisioner_ansible_options_property_handles_cli_args(instance):  # type: ignore[no-untyped-def]  # noqa: ANN001, ANN201, D103
    instance._config.args = {"debug": True}
    x = {
        "vvv": True,
        "become": True,
        "diff": True,
        "skip-tags": "molecule-notest,notest",
    }

    assert x == instance.options


@pytest.mark.parametrize(
    "config_instance",
    ["_provisioner_section_data"],  # noqa: PT007
    indirect=True,
)
def test_provisioner_env_property(instance):  # type: ignore[no-untyped-def]  # noqa: ANN001, ANN201, D103
    x = instance._config.provisioner.config_file

    assert x == instance.env["ANSIBLE_CONFIG"]
    assert instance.env["FOO"] == "bar"


@pytest.mark.parametrize(
    "config_instance",
    ["_provisioner_section_data"],  # noqa: PT007
    indirect=True,
)
def test_env_appends_env_property(instance):  # type: ignore[no-untyped-def]  # noqa: ANN001, ANN201, D103
    x = instance._get_modules_directories()
    x.append(
        util.abs_path(
            os.path.join(instance._config.scenario.directory, "foo", "bar"),  # noqa: PTH118
        ),
    )
    assert x == instance.env["ANSIBLE_LIBRARY"].split(":")

    x = [
        instance._get_filter_plugin_directory(),
        util.abs_path(
            os.path.join(  # noqa: PTH118
                instance._config.scenario.ephemeral_directory,
                "plugins",
                "filter",
            ),
        ),
        util.abs_path(
            os.path.join(instance._config.project_directory, "plugins", "filter"),  # noqa: PTH118
        ),
        util.abs_path(
            os.path.join(  # noqa: PTH118
                os.path.expanduser("~"),  # noqa: PTH111
                ".ansible",
                "plugins",
                "filter",
            ),
        ),
        "/usr/share/ansible/plugins/filter",
        util.abs_path(
            os.path.join(instance._config.scenario.directory, "foo", "bar"),  # noqa: PTH118
        ),
    ]
    assert x == instance.env["ANSIBLE_FILTER_PLUGINS"].split(":")


@pytest.mark.parametrize(
    "config_instance",
    ["_provisioner_section_data"],  # noqa: PT007
    indirect=True,
)
def test_host_vars_property(instance):  # type: ignore[no-untyped-def]  # noqa: ANN001, ANN201, D103
    x = {"instance-1": [{"foo": "bar"}], "localhost": [{"foo": "baz"}]}

    assert x == instance.host_vars


@pytest.mark.parametrize(
    "config_instance",
    ["_provisioner_section_data"],  # noqa: PT007
    indirect=True,
)
def test_group_vars_property(instance):  # type: ignore[no-untyped-def]  # noqa: ANN001, ANN201, D103
    x = {"example_group1": [{"foo": "bar"}], "example_group2": [{"foo": "bar"}]}

    assert x == instance.group_vars


@pytest.mark.parametrize(
    "config_instance",
    ["_provisioner_section_data"],  # noqa: PT007
    indirect=True,
)
def test_hosts_property(instance):  # type: ignore[no-untyped-def]  # noqa: ANN001, ANN201, D103
    hosts = {
        "all": {
            "hosts": {"extra-host-01": {}},
            "children": {"extra-group": {"hosts": ["extra-host-01"]}},
        },
    }

    assert hosts == instance.hosts


def test_links_property(instance):  # type: ignore[no-untyped-def]  # noqa: ANN001, ANN201, D103
    assert {} == instance.links


def test_inventory_directory_property(instance):  # type: ignore[no-untyped-def]  # noqa: ANN001, ANN201, D103
    x = os.path.join(instance._config.scenario.ephemeral_directory, "inventory")  # noqa: PTH118
    assert x == instance.inventory_directory


def test_inventory_file_property(instance):  # type: ignore[no-untyped-def]  # noqa: ANN001, ANN201, D103
    x = os.path.join(  # noqa: PTH118
        instance._config.scenario.inventory_directory,
        "ansible_inventory.yml",
    )

    assert x == instance.inventory_file


def test_config_file_property(instance):  # type: ignore[no-untyped-def]  # noqa: ANN001, ANN201, D103
    x = os.path.join(instance._config.scenario.ephemeral_directory, "ansible.cfg")  # noqa: PTH118

    assert x == instance.config_file


def test_playbooks_property(instance):  # type: ignore[no-untyped-def]  # noqa: ANN001, ANN201, D103
    assert isinstance(instance.playbooks, ansible_playbooks.AnsiblePlaybooks)


def test_provisioner_directory_property(instance):  # type: ignore[no-untyped-def]  # noqa: ANN001, ANN201, D103
    result = instance.directory
    parts = os_split(result)

    assert parts[-3:] == ("molecule", "provisioner", "ansible")


def test_playbooks_cleaned_property_is_optional(instance):  # type: ignore[no-untyped-def]  # noqa: ANN001, ANN201, D103
    assert instance.playbooks.cleanup is None


def test_playbooks_converge_property(instance):  # type: ignore[no-untyped-def]  # noqa: ANN001, ANN201, D103
    x = os.path.join(instance._config.scenario.directory, "converge.yml")  # noqa: PTH118

    assert x == instance.playbooks.converge


def test_playbooks_side_effect_property(instance):  # type: ignore[no-untyped-def]  # noqa: ANN001, ANN201, D103
    assert instance.playbooks.side_effect is None


def test_check(instance, mocker: MockerFixture, _patched_ansible_playbook):  # type: ignore[no-untyped-def]  # noqa: ANN001, ANN201, PT019, ARG001, D103
    instance.check()

    _patched_ansible_playbook.assert_called_once_with(
        instance._config.provisioner.playbooks.converge,
        instance._config,
        False,  # noqa: FBT003
    )
    _patched_ansible_playbook.return_value.add_cli_arg.assert_called_once_with(
        "check",
        True,  # noqa: FBT003
    )
    _patched_ansible_playbook.return_value.execute.assert_called_once_with()


def test_converge(instance, mocker: MockerFixture, _patched_ansible_playbook):  # type: ignore[no-untyped-def]  # noqa: ANN001, ANN201, PT019, ARG001, D103
    result = instance.converge()

    _patched_ansible_playbook.assert_called_once_with(
        instance._config.provisioner.playbooks.converge,
        instance._config,
        False,  # noqa: FBT003
    )
    # NOTE(retr0h): This is not the true return type.  This is a mock return
    #               which didn't go through str.decode().
    assert result == b"patched-ansible-playbook-stdout"

    _patched_ansible_playbook.return_value.execute.assert_called_once_with()


def test_converge_with_playbook(  # type: ignore[no-untyped-def]  # noqa: ANN201, D103
    instance,  # noqa: ANN001
    mocker: MockerFixture,  # noqa: ARG001
    _patched_ansible_playbook,  # noqa: ANN001, PT019
):
    result = instance.converge("playbook")

    _patched_ansible_playbook.assert_called_once_with(
        "playbook",
        instance._config,
        False,  # noqa: FBT003
    )
    # NOTE(retr0h): This is not the true return type.  This is a mock return
    #               which didn't go through str.decode().
    assert result == b"patched-ansible-playbook-stdout"

    _patched_ansible_playbook.return_value.execute.assert_called_once_with()


def test_cleanup(instance, mocker: MockerFixture, _patched_ansible_playbook):  # type: ignore[no-untyped-def]  # noqa: ANN001, ANN201, PT019, ARG001, D103
    instance.cleanup()

    _patched_ansible_playbook.assert_called_once_with(
        instance._config.provisioner.playbooks.cleanup,
        instance._config,
        False,  # noqa: FBT003
    )
    _patched_ansible_playbook.return_value.execute.assert_called_once_with()


def test_destroy(instance, mocker: MockerFixture, _patched_ansible_playbook):  # type: ignore[no-untyped-def]  # noqa: ANN001, ANN201, PT019, ARG001, D103
    instance.destroy()

    _patched_ansible_playbook.assert_called_once_with(
        instance._config.provisioner.playbooks.destroy,
        instance._config,
        False,  # noqa: FBT003
    )
    _patched_ansible_playbook.return_value.execute.assert_called_once_with()


def test_side_effect(instance, mocker: MockerFixture, _patched_ansible_playbook):  # type: ignore[no-untyped-def]  # noqa: ANN001, ANN201, PT019, ARG001, D103
    instance.side_effect()

    _patched_ansible_playbook.assert_called_once_with(
        instance._config.provisioner.playbooks.side_effect,
        instance._config,
        False,  # noqa: FBT003
    )
    _patched_ansible_playbook.return_value.execute.assert_called_once_with()


def test_create(instance, mocker: MockerFixture, _patched_ansible_playbook):  # type: ignore[no-untyped-def]  # noqa: ANN001, ANN201, PT019, ARG001, D103
    instance.create()

    _patched_ansible_playbook.assert_called_once_with(
        instance._config.provisioner.playbooks.create,
        instance._config,
        False,  # noqa: FBT003
    )
    _patched_ansible_playbook.return_value.execute.assert_called_once_with()


def test_prepare(instance, mocker: MockerFixture, _patched_ansible_playbook):  # type: ignore[no-untyped-def]  # noqa: ANN001, ANN201, PT019, ARG001, D103
    instance.prepare()

    _patched_ansible_playbook.assert_called_once_with(
        instance._config.provisioner.playbooks.prepare,
        instance._config,
        False,  # noqa: FBT003
    )
    _patched_ansible_playbook.return_value.execute.assert_called_once_with()


def test_syntax(instance, mocker: MockerFixture, _patched_ansible_playbook):  # type: ignore[no-untyped-def]  # noqa: ANN001, ANN201, PT019, ARG001, D103
    instance.syntax()

    _patched_ansible_playbook.assert_called_once_with(
        instance._config.provisioner.playbooks.converge,
        instance._config,
        False,  # noqa: FBT003
    )
    _patched_ansible_playbook.return_value.add_cli_arg.assert_called_once_with(
        "syntax-check",
        True,  # noqa: FBT003
    )
    _patched_ansible_playbook.return_value.execute.assert_called_once_with()


def test_verify(instance, mocker: MockerFixture, _patched_ansible_playbook):  # type: ignore[no-untyped-def]  # noqa: ANN001, ANN201, PT019, ARG001, D103
    instance.verify()

    if instance._config.provisioner.playbooks.verify:
        _patched_ansible_playbook.assert_called_once_with(
            instance._config.provisioner.playbooks.verify,
            instance._config,
        )
        _patched_ansible_playbook.return_value.execute.assert_called_once_with()


def test_ansible_write_config(instance):  # type: ignore[no-untyped-def]  # noqa: ANN001, ANN201, D103
    instance.write_config()

    assert os.path.isfile(instance.config_file)  # noqa: PTH113


def test_manage_inventory(  # type: ignore[no-untyped-def]  # noqa: ANN201, D103
    instance,  # noqa: ANN001
    _patched_write_inventory,  # noqa: ANN001, PT019
    _patched_remove_vars,  # noqa: ANN001, PT019
    patched_add_or_update_vars,  # noqa: ANN001
    _patched_link_or_update_vars,  # noqa: ANN001, PT019
):
    instance.manage_inventory()

    _patched_write_inventory.assert_called_once_with()
    _patched_remove_vars.assert_called_once_with()
    patched_add_or_update_vars.assert_called_once_with()
    assert not _patched_link_or_update_vars.called


def test_manage_inventory_with_links(  # type: ignore[no-untyped-def]  # noqa: ANN201, D103
    instance,  # noqa: ANN001
    _patched_write_inventory,  # noqa: ANN001, PT019
    _patched_remove_vars,  # noqa: ANN001, PT019
    patched_add_or_update_vars,  # noqa: ANN001
    _patched_link_or_update_vars,  # noqa: ANN001, PT019
):
    c = instance._config.config
    c["provisioner"]["inventory"]["links"] = {"foo": "bar"}
    instance.manage_inventory()

    _patched_write_inventory.assert_called_once_with()
    _patched_remove_vars.assert_called_once_with()
    assert not patched_add_or_update_vars.called
    _patched_link_or_update_vars.assert_called_once_with()


@pytest.mark.parametrize(
    "config_instance",
    ["_provisioner_section_data"],  # noqa: PT007
    indirect=True,
)
def test_add_or_update_vars(instance):  # type: ignore[no-untyped-def]  # noqa: ANN001, ANN201, D103
    inventory_dir = instance._config.scenario.inventory_directory

    host_vars_directory = os.path.join(inventory_dir, "host_vars")  # noqa: PTH118
    host_vars = os.path.join(host_vars_directory, "instance-1")  # noqa: PTH118

    instance._add_or_update_vars()

    assert os.path.isdir(host_vars_directory)  # noqa: PTH112
    assert os.path.isfile(host_vars)  # noqa: PTH113

    host_vars_localhost = os.path.join(host_vars_directory, "localhost")  # noqa: PTH118
    assert os.path.isfile(host_vars_localhost)  # noqa: PTH113

    group_vars_directory = os.path.join(inventory_dir, "group_vars")  # noqa: PTH118
    group_vars_1 = os.path.join(group_vars_directory, "example_group1")  # noqa: PTH118
    group_vars_2 = os.path.join(group_vars_directory, "example_group2")  # noqa: PTH118

    assert os.path.isdir(group_vars_directory)  # noqa: PTH112
    assert os.path.isfile(group_vars_1)  # noqa: PTH113
    assert os.path.isfile(group_vars_2)  # noqa: PTH113

    hosts = os.path.join(inventory_dir, "hosts")  # noqa: PTH118
    assert os.path.isfile(hosts)  # noqa: PTH113
    assert util.safe_load_file(hosts) == instance.hosts


@pytest.mark.parametrize(
    "config_instance",
    ["_provisioner_section_data"],  # noqa: PT007
    indirect=True,
)
def test_add_or_update_vars_without_host_vars(instance):  # type: ignore[no-untyped-def]  # noqa: ANN001, ANN201, D103
    c = instance._config.config
    c["provisioner"]["inventory"]["host_vars"] = {}
    inventory_dir = instance._config.scenario.inventory_directory

    host_vars_directory = os.path.join(inventory_dir, "host_vars")  # noqa: PTH118
    host_vars = os.path.join(host_vars_directory, "instance-1")  # noqa: PTH118

    instance._add_or_update_vars()

    assert not os.path.isdir(host_vars_directory)  # noqa: PTH112
    assert not os.path.isfile(host_vars)  # noqa: PTH113

    host_vars_localhost = os.path.join(host_vars_directory, "localhost")  # noqa: PTH118
    assert not os.path.isfile(host_vars_localhost)  # noqa: PTH113

    group_vars_directory = os.path.join(inventory_dir, "group_vars")  # noqa: PTH118
    group_vars_1 = os.path.join(group_vars_directory, "example_group1")  # noqa: PTH118
    group_vars_2 = os.path.join(group_vars_directory, "example_group2")  # noqa: PTH118

    assert os.path.isdir(group_vars_directory)  # noqa: PTH112
    assert os.path.isfile(group_vars_1)  # noqa: PTH113
    assert os.path.isfile(group_vars_2)  # noqa: PTH113

    hosts = os.path.join(inventory_dir, "hosts")  # noqa: PTH118
    assert os.path.isfile(hosts)  # noqa: PTH113
    assert util.safe_load_file(hosts) == instance.hosts


def test_add_or_update_vars_does_not_create_vars(instance):  # type: ignore[no-untyped-def]  # noqa: ANN001, ANN201, D103
    c = instance._config.config
    c["provisioner"]["inventory"]["hosts"] = {}
    c["provisioner"]["inventory"]["host_vars"] = {}
    c["provisioner"]["inventory"]["group_vars"] = {}
    inventory_dir = instance._config.scenario.inventory_directory

    hosts = os.path.join(inventory_dir, "hosts")  # noqa: PTH118
    host_vars_directory = os.path.join(inventory_dir, "host_vars")  # noqa: PTH118
    group_vars_directory = os.path.join(inventory_dir, "group_vars")  # noqa: PTH118

    instance._add_or_update_vars()

    assert not os.path.isdir(host_vars_directory)  # noqa: PTH112
    assert not os.path.isdir(group_vars_directory)  # noqa: PTH112
    assert not os.path.isfile(hosts)  # noqa: PTH113


@pytest.mark.parametrize(
    "config_instance",
    ["_provisioner_section_data"],  # noqa: PT007
    indirect=True,
)
def test_remove_vars(instance):  # type: ignore[no-untyped-def]  # noqa: ANN001, ANN201, D103
    inventory_dir = instance._config.scenario.inventory_directory

    hosts = os.path.join(inventory_dir, "hosts")  # noqa: PTH118
    host_vars_directory = os.path.join(inventory_dir, "host_vars")  # noqa: PTH118
    host_vars = os.path.join(host_vars_directory, "instance-1")  # noqa: PTH118

    instance._add_or_update_vars()
    assert os.path.isfile(hosts)  # noqa: PTH113
    assert os.path.isdir(host_vars_directory)  # noqa: PTH112
    assert os.path.isfile(host_vars)  # noqa: PTH113

    host_vars_localhost = os.path.join(host_vars_directory, "localhost")  # noqa: PTH118
    assert os.path.isfile(host_vars_localhost)  # noqa: PTH113

    group_vars_directory = os.path.join(inventory_dir, "group_vars")  # noqa: PTH118
    group_vars_1 = os.path.join(group_vars_directory, "example_group1")  # noqa: PTH118
    group_vars_2 = os.path.join(group_vars_directory, "example_group2")  # noqa: PTH118

    assert os.path.isdir(group_vars_directory)  # noqa: PTH112
    assert os.path.isfile(group_vars_1)  # noqa: PTH113
    assert os.path.isfile(group_vars_2)  # noqa: PTH113

    instance._remove_vars()

    assert not os.path.isfile(hosts)  # noqa: PTH113
    assert not os.path.isdir(host_vars_directory)  # noqa: PTH112
    assert not os.path.isdir(group_vars_directory)  # noqa: PTH112


def test_remove_vars_symlinks(instance):  # type: ignore[no-untyped-def]  # noqa: ANN001, ANN201, D103
    inventory_dir = instance._config.scenario.inventory_directory

    source_group_vars = os.path.join(inventory_dir, os.path.pardir, "group_vars")  # noqa: PTH118
    target_group_vars = os.path.join(inventory_dir, "group_vars")  # noqa: PTH118
    os.mkdir(source_group_vars)  # noqa: PTH102
    os.symlink(source_group_vars, target_group_vars)

    instance._remove_vars()

    assert not os.path.lexists(target_group_vars)


def test_link_vars(instance):  # type: ignore[no-untyped-def]  # noqa: ANN001, ANN201, D103
    c = instance._config.config
    c["provisioner"]["inventory"]["links"] = {
        "hosts": "../hosts",
        "group_vars": "../group_vars",
        "host_vars": "../host_vars",
    }
    inventory_dir = instance._config.scenario.inventory_directory
    scenario_dir = instance._config.scenario.directory
    source_hosts = os.path.join(scenario_dir, os.path.pardir, "hosts")  # noqa: PTH118
    target_hosts = os.path.join(inventory_dir, "hosts")  # noqa: PTH118
    source_group_vars = os.path.join(scenario_dir, os.path.pardir, "group_vars")  # noqa: PTH118
    target_group_vars = os.path.join(inventory_dir, "group_vars")  # noqa: PTH118
    source_host_vars = os.path.join(scenario_dir, os.path.pardir, "host_vars")  # noqa: PTH118
    target_host_vars = os.path.join(inventory_dir, "host_vars")  # noqa: PTH118

    open(source_hosts, "w").close()  # pylint: disable=consider-using-with  # noqa: PTH123
    os.mkdir(source_group_vars)  # noqa: PTH102
    os.mkdir(source_host_vars)  # noqa: PTH102

    instance._link_or_update_vars()

    assert os.path.lexists(target_hosts)
    assert os.path.lexists(target_group_vars)
    assert os.path.lexists(target_host_vars)


def test_link_vars_raises_when_source_not_found(instance, caplog):  # type: ignore[no-untyped-def]  # noqa: ANN001, ANN201, D103
    c = instance._config.config
    c["provisioner"]["inventory"]["links"] = {"foo": "../bar"}

    with pytest.raises(SystemExit) as e:
        instance._link_or_update_vars()

    assert e.value.code == 1

    source = os.path.join(  # noqa: PTH118
        instance._config.scenario.directory,
        os.path.pardir,
        "bar",
    )
    msg = f"The source path '{source}' does not exist."
    assert msg in caplog.text


def test_verify_inventory(instance):  # type: ignore[no-untyped-def]  # noqa: ANN001, ANN201, D103
    instance._verify_inventory()


def test_verify_inventory_raises_when_missing_hosts(  # type: ignore[no-untyped-def]  # noqa: ANN201, D103
    caplog,  # noqa: ANN001
    instance,  # noqa: ANN001
):
    instance._config.config["platforms"] = []
    with pytest.raises(SystemExit) as e:
        instance._verify_inventory()

    assert e.value.code == 1

    msg = "Instances missing from the 'platform' section of molecule.yml."
    assert msg in caplog.text


def test_vivify(instance):  # type: ignore[no-untyped-def]  # noqa: ANN001, ANN201, D103
    d = instance._vivify()
    d["bar"]["baz"] = "qux"

    assert str(d["bar"]["baz"]) == "qux"


def test_default_to_regular(instance):  # type: ignore[no-untyped-def]  # noqa: ANN001, ANN201, D103
    d = collections.defaultdict()  # type: ignore[var-annotated]
    assert isinstance(d, collections.defaultdict)

    d = instance._default_to_regular(d)
    assert isinstance(d, dict)


def test_get_plugin_directory(instance):  # type: ignore[no-untyped-def]  # noqa: ANN001, ANN201, D103
    result = instance._get_plugin_directory()
    parts = os_split(result)

    assert parts[-4:] == ("molecule", "provisioner", "ansible", "plugins")


def test_get_modules_directories_default(
    instance: ansible.Ansible,
    monkeypatch: pytest.MonkeyPatch,
    test_cache_path: Path,
) -> None:
    """Test the default module directories.

    Args:
        instance: The instance of the config.
        monkeypatch: The monkeypatch fixture.
        test_cache_path: The path to the cache directory for the test.
    """
    monkeypatch.delenv("ANSIBLE_LIBRARY", raising=False)

    paths = instance._get_modules_directories()
    number_paths = 5
    assert len(paths) == number_paths
    assert paths[0].endswith("molecule/provisioner/ansible/plugins/modules")
    assert paths[1] == f"{test_cache_path}/library"
    assert paths[2] == f"{test_cache_path}/library"
    assert paths[3].endswith(".ansible/plugins/modules")
    assert paths[4] == "/usr/share/ansible/plugins/modules"


def test_get_modules_directories_single_ansible_library(instance, monkeypatch):  # type: ignore[no-untyped-def]  # noqa: ANN001, ANN201, D103
    monkeypatch.setenv("ANSIBLE_LIBRARY", "/abs/path/lib")

    paths = instance._get_modules_directories()

    assert len(paths) == 6  # noqa: PLR2004
    assert paths[0] == "/abs/path/lib"


def test_get_modules_directories_multi_ansible_library(instance, monkeypatch):  # type: ignore[no-untyped-def]  # noqa: ANN001, ANN201, D103
    monkeypatch.setenv("ANSIBLE_LIBRARY", "relpath/lib:/abs/path/lib")

    paths = instance._get_modules_directories()

    assert len(paths) == 7  # noqa: PLR2004
    assert paths[0].endswith("relpath/lib")
    assert paths[1] == "/abs/path/lib"


def test_get_filter_plugin_directory(instance):  # type: ignore[no-untyped-def]  # noqa: ANN001, ANN201, D103
    result = instance._get_filter_plugin_directory()
    parts = os_split(result)
    x = ("molecule", "provisioner", "ansible", "plugins", "filter")

    assert x == parts[-5:]


def test_get_filter_plugins_directories_default(instance, monkeypatch, test_cache_path: Path):  # type: ignore[no-untyped-def]  # noqa: ANN001, ANN201, D103
    monkeypatch.delenv("ANSIBLE_FILTER_PLUGINS", raising=False)

    paths = instance._get_filter_plugins_directories()

    number_paths = 5
    assert len(paths) == number_paths
    assert paths[0].endswith("molecule/provisioner/ansible/plugins/filter")
    assert paths[1] == f"{test_cache_path}/plugins/filter"
    assert paths[2] == f"{test_cache_path}/plugins/filter"
    assert paths[3].endswith(".ansible/plugins/filter")
    assert paths[4] == "/usr/share/ansible/plugins/filter"


def test_get_filter_plugins_directories_single_ansible_filter_plugins(  # type: ignore[no-untyped-def]  # noqa: ANN201, D103
    instance,  # noqa: ANN001
    monkeypatch,  # noqa: ANN001
):
    monkeypatch.setenv("ANSIBLE_FILTER_PLUGINS", "/abs/path/plugins/filter")

    paths = instance._get_filter_plugins_directories()

    assert len(paths) == 6  # noqa: PLR2004
    assert paths[0] == "/abs/path/plugins/filter"


def test_get_filter_plugins_directories_multi_ansible_filter_plugins(  # type: ignore[no-untyped-def]  # noqa: ANN201, D103
    instance,  # noqa: ANN001
    monkeypatch,  # noqa: ANN001
):
    monkeypatch.setenv(
        "ANSIBLE_FILTER_PLUGINS",
        "relpath/plugins/filter:/abs/path/plugins/filter",
    )

    paths = instance._get_filter_plugins_directories()

    assert len(paths) == 7  # noqa: PLR2004
    assert paths[0].endswith("relpath/plugins/filter")
    assert paths[1] == "/abs/path/plugins/filter"


def test_absolute_path_for(instance):  # type: ignore[no-untyped-def]  # noqa: ANN001, ANN201, D103
    env = {"foo": "foo:bar"}
    x = ":".join(
        [
            os.path.join(instance._config.scenario.directory, "foo"),  # noqa: PTH118
            os.path.join(instance._config.scenario.directory, "bar"),  # noqa: PTH118
        ],
    )

    assert x == instance._absolute_path_for(env, "foo")


def test_absolute_path_for_raises_with_missing_key(instance):  # type: ignore[no-untyped-def]  # noqa: ANN001, ANN201, D103
    env = {"foo": "foo:bar"}

    with pytest.raises(KeyError):
        instance._absolute_path_for(env, "invalid")