"""This module contains pydantic specific directives.

"""
from typing import Tuple

from docutils.parsers.rst.directives import unchanged
from sphinx.addnodes import (
    desc_signature,
    desc_annotation
)
from sphinx.domains.python import PyMethod, PyAttribute, PyClasslike
from sphinxcontrib.autodoc_pydantic.inspection import ModelWrapper
from sphinxcontrib.autodoc_pydantic.util import (
    PydanticAutoDirective,
    option_default_true,
    option_list_like,
    create_field_href, remove_node_by_tagname
)

TUPLE_STR = Tuple[str, str]


class PydanticDirectiveBase:
    """Base class for pydantic directive providing common functionality.

    """

    config_name: str
    default_prefix: str

    def __init__(self, *args):
        super().__init__(*args)
        self.pyautodoc = PydanticAutoDirective(self)

    def get_signature_prefix(self, sig: str) -> str:
        """Overwrite original signature prefix with custom pydantic ones.

        """

        config_name = f"{self.config_name}-signature-prefix"
        prefix = self.pyautodoc.get_option_value(config_name)
        value = prefix or self.default_prefix
        return f"{value} "


class PydanticModel(PydanticDirectiveBase, PyClasslike):
    """Specialized directive for pydantic models.

    """

    option_spec = PyClasslike.option_spec.copy()
    option_spec.update({"__doc_disable_except__": option_list_like,
                        "model-signature-prefix": unchanged})

    config_name = "model"
    default_prefix = "class"


class PydanticSettings(PydanticDirectiveBase, PyClasslike):
    """Specialized directive for pydantic settings.

    """

    option_spec = PyClasslike.option_spec.copy()
    option_spec.update({"__doc_disable_except__": option_list_like,
                        "settings-signature-prefix": unchanged})

    config_name = "settings"
    default_prefix = "class"


class PydanticField(PydanticDirectiveBase, PyAttribute):
    """Specialized directive for pydantic fields.

    """

    option_spec = PyAttribute.option_spec.copy()
    option_spec.update({"field-show-alias": option_default_true,
                        "__doc_disable_except__": option_list_like,
                        "field-signature-prefix": unchanged})

    config_name = "field"
    default_prefix = "attribute"

    @staticmethod
    def add_alias(signode: desc_signature):
        """Replaces the return node with references to validated fields.

        """

        # get imports, names and fields of validator
        field_name = signode["fullname"].split(".")[-1]
        wrapper = ModelWrapper.from_signode(signode)
        field = wrapper.get_field_object_by_name(field_name)
        alias = field.alias

        if alias != field_name:
            signode += desc_annotation("", f" (alias '{alias}')")

    def handle_signature(self, sig: str, signode: desc_signature) -> TUPLE_STR:
        """Optionally call add alias method.

        """

        fullname, prefix = super().handle_signature(sig, signode)

        if self.pyautodoc.get_option_value("field-show-alias"):
            self.add_alias(signode)

        return fullname, prefix


class PydanticValidator(PydanticDirectiveBase, PyMethod):
    """Specialized directive for pydantic validators.

    """

    option_spec = PyMethod.option_spec.copy()
    option_spec.update({"validator-replace-signature": option_default_true,
                        "__doc_disable_except__": option_list_like,
                        "validator-signature-prefix": unchanged})

    config_name = "validator"
    default_prefix = "classmethod"

    def replace_return_node(self, signode: desc_signature):
        """Replaces the return node with references to validated fields.

        """

        remove_node_by_tagname(signode.children, "desc_parameterlist")

        # replace nodes
        class_name = "autodoc_pydantic_validator_arrow"
        signode += desc_annotation("", "  »  ", classes=[class_name])

        # get imports, names and fields of validator
        validator_name = signode["fullname"].split(".")[-1]
        wrapper = ModelWrapper.from_signode(signode)
        fields = wrapper.get_fields_for_validator(validator_name)

        # add field reference nodes
        first_field = fields[0]
        signode += create_field_href(first_field, env=self.env)
        for field in fields[1:]:
            signode += desc_annotation("", ", ")
            signode += create_field_href(field, self.env)

    def handle_signature(self, sig: str, signode: desc_signature) -> TUPLE_STR:
        """Optionally call replace return node method.

        """

        fullname, prefix = super().handle_signature(sig, signode)

        if self.pyautodoc.get_option_value("validator-replace-signature"):
            self.replace_return_node(signode)

        return fullname, prefix


class PydanticConfigClass(PydanticDirectiveBase, PyClasslike):
    """Specialized directive for pydantic config class.

    """

    option_spec = PyClasslike.option_spec.copy()
    option_spec.update({"__doc_disable_except__": option_list_like,
                        "config-signature-prefix": unchanged})

    config_name = "config"
    default_prefix = "class"
