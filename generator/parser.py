import logging

import requests
from lxml import html
from lxml.html import HtmlElement

from generator.consts import (
    ANCHOR_HEADER_PATTERN,
    DOCS_URL,
    SPECIAL_CLIENT_SUBTYPES,
    SPECIAL_SERVER_SUBTYPES,
)
from generator.normalizers import (
    normalize_description,
    normalize_method_annotation,
    normalize_type_annotation,
)
from generator.structures import Annotation, Entity, Group

log = logging.getLogger(__name__)


class Parser:
    def __init__(self):
        self.docs = self.load(DOCS_URL)
        self.groups = []

    @staticmethod
    def load_page(url: str) -> str:
        log.info("Load page %r", url)
        response = requests.get(url)
        response.raise_for_status()
        return response.text

    @staticmethod
    def to_html(content: str, url: str) -> HtmlElement:
        page = html.fromstring(content, url)

        for br in page.xpath("*//br"):
            br.tail = "\n" + br.tail if br.tail else "\n"

        return page

    def load(self, url: str) -> HtmlElement:
        content = self.load_page(url)
        return self.to_html(content, url)

    def optimize_group(self, group: Group):
        if not group.childs:
            log.warning("Remove empty %s", group)
            self.groups.remove(group)
            return

        if not group.childs[0].annotations:
            log.warning(
                "Update group %r description from first child element", group.title
            )
            group.description = group.childs[0].description
            group.childs.pop(0)

    def parse(self):
        self.groups.clear()

        group = None

        for item in self.docs.xpath("//a[@class='anchor']"):  # type: HtmlElement
            parent_tag: HtmlElement = item.getparent()
            anchor_name = item.get("name", None)
            matches = ANCHOR_HEADER_PATTERN.match(parent_tag.tag)
            if not matches or not anchor_name:
                continue
            level = int(matches.group(1))
            title = item.tail

            if level == 3:
                if group:
                    self.optimize_group(group)

                log.info("Parse group %r (#%s)", title, anchor_name)
                group = Group(title=title, anchor=anchor_name)
                self.groups.append(group)

            if level == 4 and len(title.split()) > 1:
                continue

            elif anchor_name not in [
                "recent-changes",
                "authorizing-your-bot",
                "making-requests",
            ]:
                child = self._parse_child(parent_tag, anchor_name)
                group.childs.append(child)

        if group:  # Optimize last group
            self.optimize_group(group)

        return self.groups

    def _parse_child(self, start_tag: HtmlElement, anchor: str):
        name = start_tag.text_content()
        description = []
        annotations = []

        is_method = name[0].islower()

        log.info("Parse block: %r (#%s)", name, anchor)

        for item in self._parse_tags_group(start_tag):
            if item.tag == "table":
                for raw in self._parse_table(item):
                    if is_method:
                        normalize_method_annotation(raw)
                    else:
                        normalize_type_annotation(raw)
                    annotations.append(Annotation(**raw))

            elif item.tag == "p":
                description.extend(item.text_content().splitlines())
            elif item.tag == "blockquote":
                description.extend(self._parse_blockquote(item))
            elif item.tag == "ul":
                description.extend(self._parse_list(item))

        description = normalize_description("\n".join(description))
        block = Entity(
            anchor=anchor, name=name, description=description, annotations=annotations
        )
        self._set_specific_entity_attributes(block)
        block.fix_annotations_ordering()
        log.info("%s", block)
        return block

    def _set_specific_entity_attributes(self, entity: Entity):
        if not entity.annotations:
            return
        if entity.is_type:
            return self._set_specific_type_attributes(entity)
        return self._set_specific_method_attributes(entity)

    def _set_specific_type_attributes(self, entity: Entity):
        for (
            (subtype_prefix, subtype_suffix),
            base_type,
        ) in SPECIAL_SERVER_SUBTYPES.items():
            if not (
                entity.name.startswith(subtype_prefix)
                and entity.name.endswith(subtype_suffix)
            ):
                continue
            log.info("Handled specific type %r based on %r", entity.name, base_type)
            entity.extends = [base_type]
            return

        for special_subtype_prefix, const_field in SPECIAL_CLIENT_SUBTYPES.items():
            if (
                not entity.name.startswith(special_subtype_prefix)
                or entity.name == special_subtype_prefix
            ):
                continue
            log.info(
                "Handled specific type %r based on %r",
                entity.name,
                special_subtype_prefix,
            )
            entity.extends = [special_subtype_prefix]
            for annotation in entity.annotations:
                if annotation.name != const_field:
                    continue
                annotation.const = annotation.description.rsplit(maxsplit=1)[-1].strip(
                    "'"
                )
                log.info(
                    "Setup constant field %r to %r", annotation.name, annotation.const
                )
                break

            break

    def _set_specific_method_attributes(self, entity: Entity):
        pass

    def _parse_tags_group(self, start_tag: HtmlElement):
        tag: HtmlElement = start_tag.getnext()
        while tag is not None and tag.tag not in ["h3", "h4"]:
            yield tag
            tag: HtmlElement = tag.getnext()

    def _parse_table(self, table: HtmlElement):
        head, body = table.getchildren()  # type: HtmlElement, HtmlElement
        header = [item.text_content() for item in head.getchildren()[0]]

        for body_item in body:
            yield {
                k: v
                for k, v in zip(header, [item.text_content() for item in body_item])
            }

    def _parse_blockquote(self, blockquote: HtmlElement):
        for item in blockquote.getchildren():
            yield from item.text_content().splitlines()

    def _parse_list(self, data: HtmlElement):
        for item in data.getchildren():
            yield " - " + item.text_content()
